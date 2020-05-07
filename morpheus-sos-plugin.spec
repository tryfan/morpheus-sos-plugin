%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Summary:       Sosreport plugin to gather data about Morpheus and components
Name:          morpheus-sos-plugin
Version:       0.0.1
Release:       0%{?build_id:.%build_id}%{?dist}
License:       MIT
Group:         Applications/System
Url:           http://github.com/tryfan/morpheus-sos-plugin
BuildArch:     noarch

BuildRequires: python2-devel
BuildRequires: python-setuptools
Requires:      sos >= 3
Source0:       %{tarball_basedir}.tar.gz

%description
Sosreport is a collection of scripts that gathers system and configuration information.
This package contains the Morpheus plugin for sosreport to send to support when diagnosing issues.

%prep
%setup -q -n %{tarball_basedir}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install --skip-build --root $RPM_BUILD_ROOT
rm $RPM_BUILD_ROOT/%{python_sitelib}/sos/plugins/__init__.py*
rm $RPM_BUILD_ROOT/%{python_sitelib}/sos/__init__.py*

%files
%defattr(-,root,root,-)
%{python_sitelib}/sos/plugins/*
%{python_sitelib}/*.egg-info

%changelog
* Mon May 07 2020 Nick Celebic <nick@celebic.net> - 0.0.1
- First build
