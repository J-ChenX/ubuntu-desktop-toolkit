# 贡献指南

欢迎通过 Issue 报告问题、通过 Pull Request 提交改动。请提供 Ubuntu/桌面/应用版本、复现步骤与预期结果；日志先移除用户名、目录和凭据。

## 本地检查

```bash
./desktopctl check
python3 tests/test-management.py
python3 tests/test-repository.py
```

Rust 构建工具链固定为 1.98.1，管理器依赖已 vendor；安装该工具链后执行 `scripts/build-native.sh`。该脚本更新管理器二进制并测试核心；审核产物后运行 `python3 scripts/update-checksums.py`，再次运行上述检查。交互改动还需 Ubuntu 22.04 私有测试会话中的 `tests/run-ui.sh`；不能仅依赖 CI。

## 文件管理

字体、搜狗安装包、本机备份、下载目录、构建缓存和凭据不提交 Git。修改配置/源码/文档后更新 SHA256SUMS；安装包变动还需更新发布 manifest、版本、对应完整源码及验证记录。不要用重新生成校验值来掩盖不明文件来源。

新增代码遵循 THIRD_PARTY_NOTICES.md 中相应组件许可。保留第三方版权声明与许可证。自制补丁包目前随对应源码快照分发，字体/搜狗从官方单独下载。
