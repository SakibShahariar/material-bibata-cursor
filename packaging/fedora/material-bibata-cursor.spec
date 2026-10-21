Name:           material-bibata-cursor
Version:        1.5.0
Release:        1%{?dist}
Summary:        Material Design 3 Bibata cursor themes
License:        MIT AND GPL-3.0-or-later
URL:            https://github.com/SakibShahariar/material-bibata-cursor
BuildArch:      noarch
Requires:       hicolor-icon-theme

Source0:        https://github.com/SakibShahariar/material-bibata-cursor/releases/download/v%{version}/bibata-material-dark-v%{version}.tar.gz
Source1:        https://github.com/SakibShahariar/material-bibata-cursor/releases/download/v%{version}/bibata-material-light-v%{version}.tar.gz
Source2:        https://www.gnu.org/licenses/gpl-3.0.txt

%description
Material Bibata Cursor provides 57 cursor themes: 28 dark palettes, 28
matching light palettes, and the original Classic theme. The release
archives contain Xcursor, scalable SVG, and Hyprcursor assets.

%prep
%setup -q -c -T
mkdir dark light
tar -xzf %{SOURCE0} -C dark --strip-components=1
tar -xzf %{SOURCE1} -C light --strip-components=1

%build
# The upstream release archives contain prebuilt cursor assets.

%install
install -d %{buildroot}%{_datadir}/icons
find dark light -mindepth 1 -maxdepth 1 -type d -name 'Bibata-Material-*' \
    -exec cp -a '{}' %{buildroot}%{_datadir}/icons/ \;

install -Dpm 0644 dark/LICENSE \
    %{buildroot}%{_licensedir}/%{name}/LICENSE
install -Dpm 0644 %{SOURCE2} \
    %{buildroot}%{_licensedir}/%{name}/GPL-3.0.txt
install -Dpm 0644 dark/CREDITS.txt \
    %{buildroot}%{_licensedir}/%{name}/CREDITS.txt
install -Dpm 0644 dark/README.md \
    %{buildroot}%{_docdir}/%{name}/README.md

%files
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/GPL-3.0.txt
%license %{_licensedir}/%{name}/CREDITS.txt
%doc %{_docdir}/%{name}/README.md
%{_datadir}/icons/Bibata-Material-*

%changelog
* Wed Oct 21 2026 Sakib Shahariar <74959773+SakibShahariar@users.noreply.github.com> - 1.5.0-1
- Initial Fedora RPM packaging using the upstream release archives.
