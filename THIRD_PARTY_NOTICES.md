# 许可证与第三方组件

项目维护者：Nix Jiang <jiang.cxin@gmail.com>。

本项目新增代码、脚本与文档默认采用 **GPL-3.0-or-later**，完整许可证见 `LICENSE`。以下独立组件遵循各自许可证，不因本仓库的默认许可被重新许可：

| 内容 | 许可证与来源 |
|---|---|
| `src/desktopctl/` 自有代码、`bin/desktopctl` | MIT，见 `LICENSES/MIT.txt`；依赖分别遵循 `vendor/` 内许可证与 Cargo 元数据 |
| `src/selection-core/`、Nautilus 适配补丁 | GPL-3.0-or-later |
| Nautilus 完整源码与定制 Debian 包 | GNOME Nautilus / Ubuntu 42.6；见源码归档内 `LICENSE`、`debian/copyright` 及各文件声明；完整对应源码随包提供 |
| GTK3/GTK4 点击路径模块自有实现 | GPL-3.0-or-later；链接系统 GTK，GTK 本身遵循其上游 LGPL 许可证 |
| Maple Mono 字体 | SIL OFL 1.1，见 `modules/terminal/fonts/LICENSE.txt`；字体下载文件不在 Git 中 |
| 搜狗拼音 | 专有软件，遵循搜狗许可；本项目仅提供下载及配置方法，不重新分发或重新许可 |
| Terminator、Fcitx、GTK、其他系统依赖 | 由 Ubuntu 仓库安装，分别遵循其上游许可证 |

Nautilus 来源：https://gitlab.gnome.org/GNOME/nautilus 。定制源码快照位于 `modules/file-manager/release/source/`，包含本项目发布包对应的修改和 Debian 构建材料；上游版权声明保留。Rust 依赖的版本与来源由 Cargo.lock 锁定，vendor 中保留原许可文件。
