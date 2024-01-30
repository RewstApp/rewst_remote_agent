Name:           rewst_remote_agent
Version:        %VERSION%
Release:        1%{?dist}
Summary:        An RMM-agnostic remote agent using the Azure IoT Hub

License:        GPLv3
URL:            https://github.com/rewstapp/rewst_remote_agent

BuildRequires:  python3-devel
Requires:       python3

%description
rewst_remote_agent is an RMM-agnostic remote agent that leverages Azure IoT Hub.

%prep
%setup -q

%build
python setup.py build

%install
python setup.py install --root=$RPM_BUILD_ROOT

%files
`find $RPM_BUILD_ROOT -type f | sed "s#$RPM_BUILD_ROOT##g"`

%changelog
%autochangelog
