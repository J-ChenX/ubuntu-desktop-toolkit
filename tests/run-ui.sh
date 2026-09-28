#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
name=${1:-ui-test-gray.py}
case "$name" in ui-test-gray.py|ui-test-dnd.py|ui-test-selection-edges.py|ui-test-band-lifecycle.py) ;; *) exit 2 ;; esac
runtime=$(mktemp -d /tmp/udt-test.XXXXXX)
mkdir -p "$runtime"/{config,data,cache,run,tests}
chmod 700 "$runtime/run"
cp -R "$root/tests/file-manager/." "$runtime/tests/"
trap '/usr/bin/python3 "$root/scripts/cleanup-test-session.py" "$runtime/run"' EXIT
export XDG_CONFIG_HOME="$runtime/config" XDG_DATA_HOME="$runtime/data" XDG_CACHE_HOME="$runtime/cache" XDG_RUNTIME_DIR="$runtime/run"
export GSETTINGS_BACKEND=keyfile GTK_MODULES=atk-bridge GTK_IM_MODULE=gtk-im-context-simple GIO_USE_VFS=local XDG_CURRENT_DESKTOP=generic
unset AT_SPI_BUS_ADDRESS LD_PRELOAD
# Requires xvfb, xauth, xdotool, python3-pyatspi, python3-pil and matching GI libraries.
dbus-run-session -- xvfb-run -a -s '-screen 0 1600x1100x24' /usr/bin/python3 "$runtime/tests/$name" "${NAUTILUS_TEST_BINARY:-/usr/bin/nautilus}"
