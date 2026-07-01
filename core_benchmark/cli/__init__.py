# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""core_benchmark.cli — 命令行入口

提供两个入口点:
    - main(): 主 CLI(支持 run/info/config 子命令)
    - run_suite(): benchmark-run 脚本入口(run 的快捷方式)

使用示例:
    # 通过 Python 调用
    from core_benchmark.cli import main
    main(["run", "--demo", "--iterations", "50"])

    # 通过命令行调用
    benchmark run --demo --format json --output ./report.json
    benchmark info
    benchmark config
"""

from core_benchmark.cli.main import main, run_suite

__all__ = ["main", "run_suite"]
