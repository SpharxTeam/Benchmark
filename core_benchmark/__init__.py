# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
Benchmark - 独立算法基准库

提供算法性能评测框架,支持延迟/吞吐/内存/准确度基准测试,
输出 JSON/CSV/Markdown 格式报告。

核心组件:
    - core: 核心抽象(ErrorCode, 接口, 数据模型)
    - metrics: 四大度量收集器(latency/throughput/memory/accuracy)
    - runners: 基准运行器(单算法 + 多算法批量)
    - reporting: 报告生成器(JSON/CSV/Markdown)
    - cli: 命令行入口
    - config: 配置文件
"""

__version__ = "1.0.0"
__author__ = "SPHARX Team"

# 延迟导入 — 避免循环依赖,在使用时按需导入子模块
# 完整 API 导出在 core_benchmark.core 中定义

__all__ = ["__version__", "__author__"]
