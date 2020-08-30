#
# spec file for package zrepl
#
# https://github.com/zrepl/zrepl
#
#
# Background
# ----------
# This spec file was written primarily for Fedora Linux, with minor tweaks to
# enable builds for RedHat/CentOS and openSUSE. Thus, the spec file follows
# mainly the recommendations in the Go packaging guidelines for Fedora [1] and
# openSUSE [2].
#
#
# Build dependencies
# ------------------
# The Fedora packaging guidelines for Go [1] state that packages should be
# unbundled by default, i.e. dependencies should be packaged separately and
# included as `BuildRequires` in the spec file.
# `BuildRequires` can be automatically generated using the following go-rpm
# macros during the prep stage, which in turn invokes `golist`:
#   %%generate_buildrequires
#   %%go_generate_buildrequires
# However, this requires that all dependencies are packaged, which currently
# (Aug 2020) is not the case for Fedora/RedHat. Missing dependencies are:
#   golang(github.com/gitchander/permutation)
#   golang(github.com/jinzhu/copier)
#   golang(github.com/problame/go-netssh)
#   golang(github.com/zrepl/yaml-config)
# The alternative solution is to have go pull the dependencies (using `golist`)
# in the build stage, which in turn requires internet access for build.
#
#
# Build
# -----
# Given that the dependencies are bundled and downloaded in the build stage, the
# default Go build macros cannot be used:
#   LDFLAGS="-X github.com/zrepl/zrepl/version.zreplVersion=%%{version} "
#   %%gobuild -o %%{gobuilddir}/bin/zrepl %%{goipath}
#
# The best/easiest way forward is to use the zrepl Makefile which ensures a
# consistent build with the upstream settings:
#   make ZREPL_VERSION=%%{version} zrepl-bin
#
#
# Distributions
# -------------
# The spec file has been tested on Fedora's copr build service [3] and is known
# to work for the following distributions:
#  - epel-8-x86_64
#  - fedora-31-x86_64
#  - fedora-32-x86_64
#  - fedora-33-x86_64
#  - fedora-rawhide-x86_64
#  - opensuse-leap-15.1-x86_64
#  - opensuse-leap-15.2-x86_64
#
#
# References
# ----------
# [1] https://docs.fedoraproject.org/en-US/packaging-guidelines/Golang/
# [2] https://en.opensuse.org/openSUSE:Packaging_Go
# [3] https://copr.fedorainfracloud.org/


# Add workaround for "No build ID note found" error during %%install
%undefine _missing_build_ids_terminate_build


# Disable debuginfo for RedHat/CentOS builds to avoid errors due to empty
# debuginfo files, see also: https://fedoraproject.org/wiki/Packaging:Debuginfo
%if 0%{?rhel}
%global debug_package %{nil}
%endif


# Global meta data
%global goipath   github.com/zrepl/zrepl
Version:          0.3.0
%if 0%{?fedora}%{?rhel} >= 8
%gometa
%endif
%global common_description %{expand:
zrepl is a one-stop, integrated solution for ZFS replication.}


Name:             zrepl
Release:          1%{?dist}
Summary:          One-stop, integrated solution for ZFS replication
License:          MIT
URL:              https://zrepl.github.io/
%if 0%{?fedora}%{?rhel} >= 8
# Fedora and RedHat/CentOS 8
Source0:          %{gosource}
%else
# openSUSE and RedHat/CentOS 7
Source0:          %{name}-%{version}.tar.gz
%endif
BuildRequires:    golang >= 1.11
%if 0%{?suse_version}
BuildRequires:    golang-packaging
%endif
BuildRequires:    git >= 2
BuildRequires:    systemd
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd


%description
%{common_description}


%gopkg


%prep
%if 0%{?fedora}
%goprep
%else
%setup -q -n %{name}-%{version}
%endif


%build
# The output directory for zrepl binaries is: artifacts/zrepl-<OS>-<ARCH>
make ZREPL_VERSION=%{version} zrepl-bin

# Generate the shell auto-completion files
artifacts/zrepl-linux-* gencompletion zsh  artifacts/zrepl-zsh
artifacts/zrepl-linux-* gencompletion bash artifacts/zrepl-bash

# Correct the path in the systemd unit file
sed s:/usr/local/bin/:%{_bindir}/:g dist/systemd/zrepl.service > artifacts/zrepl.service

# Generate the default configuration file
cat > artifacts/zrepl.yml <<-EOF
	global:
	  logging:
	    # use syslog instead of stdout because it makes journald happy
	    - type: syslog
	      format: human
	      level: warn

	jobs:
	#  - name: foo
	#    type: bar

	# see %{_datadir}/doc/zrepl/examples
	# or https://zrepl.github.io/configuration/overview.html
EOF


%install
install -Dm 0755 artifacts/zrepl-linux-*  %{buildroot}%{_bindir}/zrepl
install -Dm 0644 artifacts/zrepl.service  %{buildroot}%{_unitdir}/zrepl.service
install -Dm 0644 artifacts/zrepl-zsh      %{buildroot}%{_datadir}/zsh/site-functions/_zrepl
install -Dm 0644 artifacts/zrepl-bash     %{buildroot}%{_datadir}/bash-completion/completions/zrepl
install -Dm 0644 artifacts/zrepl.yml      %{buildroot}%{_sysconfdir}/zrepl/zrepl.yml
install -d %{buildroot}%{_datadir}/doc/zrepl/examples/hooks
install -Dm 0644 config/samples/*.*       %{buildroot}%{_datadir}/doc/zrepl/examples
install -Dm 0644 config/samples/hooks/*.* %{buildroot}%{_datadir}/doc/zrepl/examples/hooks


%post
%systemd_post zrepl.service


%preun
%systemd_preun zrepl.service


%postun
%systemd_postun_with_restart zrepl.service


%files
%defattr(-,root,root)
%license LICENSE
%{_bindir}/zrepl
%{_unitdir}/zrepl.service
%dir %{_sysconfdir}/zrepl
%{_sysconfdir}/zrepl/zrepl.yml
%{_datadir}/zsh/site-functions/_zrepl
%{_datadir}/bash-completion/completions/zrepl
%dir %{_datadir}/doc/zrepl
%dir %{_datadir}/doc/zrepl/examples
%dir %{_datadir}/doc/zrepl/examples/hooks
%{_datadir}/doc/zrepl/examples/*.*
%{_datadir}/doc/zrepl/examples/hooks/*.*


%changelog
* Fri Aug 28 2020 Armin Wehrfritz <dkxls23@gmail.com> - 0.3.0-1
- Initial package build
