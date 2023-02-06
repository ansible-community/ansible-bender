# All tests require Internet access
# to test in mock use:  --enable-network --with check
# to test in a privileged environment use:
#   --with check --with privileged_tests
%bcond_with     check
%bcond_with     privileged_tests

Name:           ansible-bender
Version:        0.10.1
Release:        1%{?dist}
Summary:        Build container images using Ansible playbooks

License:        MIT
URL:            https://github.com/ansible-community/ansible-bender
Source0:        %{pypi_source}

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-setuptools_scm
%if %{with check}
# These are required for tests:
BuildRequires:  python%{python3_pkgversion}-pyyaml
BuildRequires:  python%{python3_pkgversion}-tabulate
BuildRequires:  python%{python3_pkgversion}-jsonschema
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-flexmock
BuildRequires:  python%{python3_pkgversion}-pytest-xdist
BuildRequires:  python%{python3_pkgversion}-libselinux
BuildRequires:  ansible
BuildRequires:  podman
BuildRequires:  buildah
BuildRequires:  git
%endif
Requires:       ansible
Requires:       buildah

%description
This is a tool which bends containers using Ansible playbooks and
turns them into container images. It has a pluggable builder selection
- it is up to you to pick the tool which will be used to construct
your container image. Right now the only supported builder is
buildah. More to come in the future. Ansible-bender (ab) relies on
Ansible connection plugins for performing builds.

tl;dr Ansible is the frontend, buildah is the backend.

%prep
%autosetup


%build
%py3_build


%install
%py3_install


%if %{with check}
%check
PYTHONPATH=%{buildroot}%{python3_sitelib} \
  pytest-3 \
  -v \
  --disable-pytest-warnings \
  --numprocesses=auto \
%if %{with privileged_tests}
  tests
%else
  tests/unit
%endif
%endif


%files
%{python3_sitelib}/ansible_bender-*.egg-info/
%{python3_sitelib}/ansible_bender/
%{_bindir}/ansible-bender
%license LICENSE
%doc docs/* README.md



%changelog
* Mon Feb 06 2023 Tomas Tomecek <ttomecek@redhat.com> - 0.10.1-1
- 0.10.1 upstream release

* Fri Feb 03 2023 Tomas Tomecek <ttomecek@redhat.com> - 0.10.0-1
- 0.10.0 upstream release

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.8.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 0.8.1-3
- Rebuilt for Python 3.9

* Mon May 18 2020 Gordon Messmer <gordon.messmer@gmail.com> - 0.8.1-2
- Rebuild with fix for missing python modules.

* Mon Apr 27 2020 Gordon Messmer <gordon.messmer@gmail.com> - 0.8.1-1
- Build 0.8.1

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 0.7.0-4
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 0.7.0-3
- Rebuilt for Python 3.8

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Jul 03 2019 Gordon Messmer <gordon.messmer@gmail.com> - 0.7.0-1
- Build 0.7.0

* Tue Jul 02 2019 Gordon Messmer <gordon.messmer@gmail.com> - 0.6.1-6
- First build for Fedora
