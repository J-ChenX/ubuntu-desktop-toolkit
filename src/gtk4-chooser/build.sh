#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
cc -std=c11 -Wall -Wextra -Werror -O2 -fPIC -shared portal-click-path.c -o libportal-click-path.so $(pkg-config --cflags --libs gtk4) -Wl,-z,defs,-z,relro,-z,now -ldl
