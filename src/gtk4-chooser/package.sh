#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
package_root="$PWD/build/package"
mkdir -p "$package_root/DEBIAN" "$package_root/usr/lib/local-portal-click-path" "$package_root/usr/share/doc/local-portal-click-path"
install -m 644 libportal-click-path.so "$package_root/usr/lib/local-portal-click-path/"
install -m 644 portal-click-path.c "$package_root/usr/share/doc/local-portal-click-path/"
cat > "$package_root/DEBIAN/control" <<'CONTROL'
Package: local-portal-click-path
Version: 1.0.2
Architecture: amd64
Maintainer: Nix Jiang <jiang.cxin@gmail.com>
Depends: libgtk-4-1 (>= 4.6.9), libglib2.0-0, libc6
Section: x11
Priority: optional
Description: Click-to-edit paths for the GNOME GTK 4 file chooser portal
 Scoped integration for xdg-desktop-portal-gnome 42.1, configured per user.
 Does not replace GTK or the portal executable.
CONTROL
chmod -R go-w "$package_root"
dpkg-deb --root-owner-group --build "$package_root" "$PWD/local-portal-click-path_1.0.2_amd64.deb"
