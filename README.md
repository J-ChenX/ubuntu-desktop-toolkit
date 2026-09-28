# Ubuntu Desktop Toolkit

Ubuntu 桌面优化工具包。维护者：Nix Jiang。

用于持续改善 Ubuntu 默认桌面的操作体验，并把已验证的优化迁移到其他电脑。当前基线为 **Ubuntu 22.04 amd64、GNOME 42、Nautilus 42.6**；其他 Ubuntu 版本需要先适配源码和依赖，不能直接套用这些二进制包。

目前包含文件管理器统一补丁 v8、Terminator 终端与个人配置、搜狗拼音 4.2.1.145 的下载与安装方法。整理日期：2026-09-28。

## 已完成的优化

- **文件管理器 v8**：整项拖动、多文件拖放、剪切半透明、灰色双向框选；中键聚合并去重，中键复制标签，拖出标签拆分窗口；路径栏点击编辑、空白双击返回上级、慢速单击重命名、多选复制路径、主题终端菜单；GTK3/GTK4 文件选择弹窗地址编辑。
- **终端**：Terminator 深色主题、Maple Mono 中文字体、Ctrl+C 有选区复制／无选区中断、Ctrl+V 粘贴、清除已复制选区、10000 行回滚、Ctrl+Alt+T 入口，以及可选个人项目启动菜单。
- **中文输入**：提供搜狗拼音官方下载方法，提供 Fcitx 4、中文语言支持、环境变量、自启动和注销重登的完整安装方法。

统一入口为 **`./desktopctl`**，版本和模块位置集中在 `components.json`。`./desktopctl check` 校验完整工具包，`./desktopctl status` 只检查安装与运行状态，不扫描全部字体和输入法安装包。管理器按需运行，不新增常驻服务。

v8 已把框选纯计算提取为 Rust 核心，并加入缓存、按帧合并和差分更新；功能操作保持不变。[当前架构、性能实测与安全边界](docs/架构与安全.md)。

## 从这里开始

先按 [下载依赖](docs/下载依赖.md) 准备字体和搜狗安装包，再以自己的桌面用户执行，不要用 sudo 运行整个脚本：

```bash
git clone https://github.com/J-ChenX/ubuntu-desktop-toolkit.git ~/code/ubuntu-desktop-toolkit
cd ~/code/ubuntu-desktop-toolkit
# 按 docs/下载依赖.md 准备所选模块的下载文件
./desktopctl install all --check
./desktopctl install all
```

脚本按步骤调用 sudo 安装系统依赖，APT 会展示变更并要求确认。需要网络安装 Ubuntu 仓库依赖；工具包包含定制补丁；字体和搜狗安装包需另外下载，但不是完整离线系统镜像。安装前备份即将覆盖的用户配置，完成后保存工作、注销并重新登录。不会自动重启或关闭正在使用的窗口。

可单独安装：

```bash
./desktopctl install terminal
./desktopctl install file-manager
./desktopctl install sogou
```

可选项：

- `--selection-style`：应用本机保存的橙色 Nautilus 文件选中样式；默认保留目标电脑原样式。框选矩形为灰色，与选中样式独立。
- `--project-menu`：加入个人“示例项目启动”菜单；仅适用于存在 `~/code/example-project` 项目的电脑。默认不加此项目专用入口，示例配置已保留。

```bash
./desktopctl install all --selection-style --project-menu
./desktopctl status
```

运行安装器会替换目标用户的 Terminator 配置，旧配置有备份。若只想阅读或复制文件，不需要执行安装脚本。安装版本与当前运行进程可能不同，可用 `./desktopctl status` 核对；更新后保存工作并注销重登。

## 内容与说明

| 内容 | 说明 |
|---|---|
| [文件管理器](docs/文件管理器.md) | 拖动、灰色方向框选、剪切透明度、标签聚合去重、中键复制标签、弹窗地址栏；包含安装包、源码、测试记录 |
| [终端与个人配置](docs/终端.md) | Terminator 深色主题、字体、复制粘贴、默认终端入口和可选项目菜单 |
| [搜狗输入法](docs/搜狗输入法.md) | Ubuntu 22.04 + Fcitx 4 安装步骤、重新登录、常见问题和官方来源 |
| [更新、同步与恢复](docs/维护与同步.md) | rsync 同步、安装核对、配置备份与恢复 |

```text
desktopctl / bin/          统一 Rust 命令入口
components.json           当前组件版本与路径清单
modules/file-manager/     唯一当前发布版 release/、可选选中样式
modules/terminal/         启动器、配置、个人菜单示例、字体下载说明及许可证
modules/input-method/     搜狗安装包下载位置（Git 忽略）
src/                      Rust 核心、GTK 适配补丁、GTK3/GTK4 弹窗模块源码
scripts/                  构建、安装、检查、配置恢复
tests/                   功能回归、管理器测试、性能测试工具
reports/                  当前发布验证记录与性能对比数据
docs/                    当前功能、安装、架构和同步说明
SHA256SUMS                工具包完整性清单
```

备份默认位于目标用户的 `~/.local/state/ubuntu-desktop-toolkit/backups/时间戳/`，不写入此工具包，也不随同步传给其他电脑。没有收录 shell 历史、SSH 密钥、搜狗账号和个人词库。

工具包仅保留当前版本，不收录旧发布包或软件降级包。第三方字体和搜狗安装包不纳入 Git；Rust 的锁定依赖、最新完整源码和字体许可证保留，支持后续构建与维护。性能记录中的 v7 数据仅作为 v8 的比较基线，不包含旧软件。

## 开源与贡献

默认采用 GPL-3.0-or-later；独立 Rust 管理器采用 MIT，第三方组件保留原许可，详见 [许可证说明](THIRD_PARTY_NOTICES.md)。

- [贡献与本地检查](CONTRIBUTING.md)
- [安全问题报告](SECURITY.md)
- [当前发布记录](CHANGELOG.md)

当前发布仅验证 Ubuntu 22.04 amd64 / GNOME 42；不代表支持所有 Ubuntu 版本。CI 检查文件完整性、管理器和 Rust 核心，不能替代真实桌面交互验收。
