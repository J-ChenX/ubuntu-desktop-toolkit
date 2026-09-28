#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root/src/desktopctl"
rustup run 1.98.1 cargo build --release --offline --locked --target-dir "$root/work/native"
install -m 755 "$root/work/native/release/desktopctl" "$root/bin/desktopctl"
cd "$root/src/selection-core"
rustup run 1.98.1 cargo test --offline --locked --target-dir "$root/work/selection"
rustup run 1.98.1 cargo clippy --offline --locked --all-targets --target-dir "$root/work/selection" -- -D warnings
printf '%s\n' '构建完成；审核后运行 scripts/update-checksums.py 更新发布校验清单。'
