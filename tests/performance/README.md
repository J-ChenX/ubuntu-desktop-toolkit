# 性能测试材料

benchmark.py：5000 个空文件，在独立图形会话中等待 CPU 稳定，再发送 600 次鼠标更新，记录进程 CPU/PSS 和截图。通过 BENCH_BINARY 指定候选二进制、PERF_OUTPUT 指定输出 JSON。必须在独立 Xvfb 与 D-Bus 会话下运行，并设置独立 XDG_CONFIG_HOME / DATA_HOME / CACHE_HOME / RUNTIME_DIR；不要直接对用户桌面运行它。需要 xdotool、python3-gi、python3-pil。它不测量实际输入到显示的延迟，也不是泄漏检测器。

kernel-benchmark.cpp：相同输入的 C++ 几何循环与 Rust C ABI 比较。将 selection-core/lib.rs 编译成 staticlib 后，用 g++ -O3 -std=c++17 链接该静态库及 -ldl -lpthread。输出是微基准，不能替代整体 GTK 性能测试；Rust 端额外保留 ABI 参数验证。

正式操作回归可使用 ../run-ui.sh，默认运行当前系统安装的 Nautilus。它创建私有图形会话与临时文件夹，并在退出时清理带有该运行目录标签的进程。测试输出留在 /tmp/udt-test.* 供诊断；不自动修改发布清单。
