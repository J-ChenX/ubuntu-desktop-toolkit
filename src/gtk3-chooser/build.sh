#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
cc -std=c11 -Wall -Wextra -Werror -O2 -fPIC -shared gtk-filechooser-click-path.c -o libgtk-filechooser-click-path.so $(pkg-config --cflags --libs gtk+-3.0 gmodule-2.0) -Wl,-z,defs,-z,relro,-z,now -ldl
