Name:           rewst_remote_agent
Version:        %VERSION%
Release:        1%{?dist}
Summary:        An RMM-agnostic remote agent using the Azure IoT Hub

License:        GPLv3
URL:            https://github.com/rewstapp/rewst_remote_agent
Source0:        https://github.com/rewstapp/rewst_remote_agent/archive/%{version}.tar.gz

BuildRequires:  python3-devel, [other build dependencies]
Requires:       python3, [other runtime dependencies]

%description
rewst_remote_agent is an RMM-agnostic remote agent that leverages Azure IoT Hub. [More detailed description]

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
