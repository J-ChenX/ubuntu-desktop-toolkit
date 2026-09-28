#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
package_root="$PWD/build/package"
mkdir -p "$package_root/DEBIAN" "$package_root/usr/lib/x86_64-linux-gnu/gtk-3.0/modules" "$package_root/usr/share/doc/local-gtk-filechooser-click-path"
mkdir -p "$package_root/usr/lib/gnome-settings-daemon-3.0/gtk-modules"
printf '%s\n' 'Refresh marker for the per-user enabled-gtk-modules setting; not an auto-enable descriptor.' > "$package_root/usr/lib/gnome-settings-daemon-3.0/gtk-modules/local-gtk-filechooser-click-path.refresh"
install -m 644 libgtk-filechooser-click-path.so "$package_root/usr/lib/x86_64-linux-gnu/gtk-3.0/modules/"
install -m 644 gtk-filechooser-click-path.c "$package_root/usr/share/doc/local-gtk-filechooser-click-path/"
cat > "$package_root/DEBIAN/control" <<'CONTROL'
Package: local-gtk-filechooser-click-path
Version: 1.0.0
Architecture: amd64
Maintainer: Nix Jiang <jiang.cxin@gmail.com>
Depends: libgtk-3-0 (>= 3.24.33), libglib2.0-0, libatk1.0-0, libc6
Section: x11
Priority: optional
Description: Local click-to-edit paths for GTK 3 file choosers
 Adds current breadcrumb and empty path bar click handling using the native
 Ctrl+L action, plus a button to return to breadcrumbs. Enabled per user.
CONTROL
chmod -R go-w "$package_root"
dpkg-deb --root-owner-group --build "$package_root" "$PWD/local-gtk-filechooser-click-path_1.0.0_amd64.deb"
