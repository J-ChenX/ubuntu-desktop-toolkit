# 当前文件管理器发布版

版本：1:42.6-0ubuntu2+localpathbar8；GTK3 点击路径模块 1.0.0，GTK4 portal 模块 1.0.2。

- `packages/`：唯一当前版本的五件套安装包。
- `manifest.json`：组件版本、安装包哈希和 Nautilus 二进制哈希。
- `source/`：完整 Nautilus v8 发布源码快照。

从工具包根目录执行 `./desktopctl install file-manager`，保存工作并注销重登生效。功能与安装见 [文件管理器说明](../../../docs/文件管理器.md)，构建与性能见 [架构与安全](../../../docs/架构与安全.md)。回归脚本集中在根目录 `tests/file-manager/`，验证记录在 `reports/validation/`。旧发布版和降级包不再收录。
