# Benchmark

> 独立算法基准库 — 提供算法性能评测框架

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

## 模块定位

Benchmark 是 SpharxTools 生态中的独立算法基准库,提供统一的算法性能评测框架,支持多种算法的延迟、吞吐、内存、准确度基准测试,输出 JSON/CSV/Markdown 格式报告。

### 核心能力

- **四大度量维度**: 延迟(latency)、吞吐(throughput)、内存(memory)、准确度(accuracy)
- **多算法批量评测**: 支持 `BenchmarkSuiteRunner` 批量运行多个算法基准
- **并行执行**: 基于 `concurrent.futures` 的并行基准测试
- **三种报告格式**: JSON / CSV / Markdown(含表格与 ASCII 图表)
- **高精度计时**: 使用 `time.perf_counter_ns()` 纳秒级精度
- **内存跟踪**: 基于 `tracemalloc` 的峰值/平均/泄漏检测
- **统计分布**: 支持 p50/p90/p99 百分位统计

## 架构

```
core_benchmark/
├── core/           # 核心抽象(ErrorCode, 接口, 数据模型)
│   ├── abstractions.py
│   ├── interfaces.py
│   └── models.py
├── metrics/        # 四大度量收集器
│   ├── latency.py
│   ├── throughput.py
│   ├── memory.py
│   └── accuracy.py
├── runners/        # 基准运行器
│   ├── base_runner.py
│   └── suite_runner.py
├── reporting/      # 报告生成器
│   ├── json_reporter.py
│   ├── csv_reporter.py
│   └── markdown_reporter.py
├── cli/            # 命令行入口
│   └── main.py
└── config/         # 配置文件
    └── default.yaml
```

## 快速开始

### 安装

```bash
cd Benchmark
pip install -e ".[dev]"
```

### 命令行使用

```bash
# 运行默认基准套件
benchmark-run --suite default

# 运行指定基准
benchmark-run --suite my_suite --output ./produce/report.json
```

### 编程式使用

```python
from core_benchmark.runners.suite_runner import BenchmarkSuiteRunner
from core_benchmark.reporting.json_reporter import JsonReporter

# 创建运行器
runner = BenchmarkSuiteRunner()

# 注册算法基准
runner.register("sort_algorithm", my_sort_benchmark)

# 运行基准
results = runner.run_all(iterations=100)

# 生成报告
reporter = JsonReporter()
reporter.generate(results, "./produce/benchmark_report.json")
```

## ErrorCode 体系

参考 Workshop WS-T01 ErrorCode v4.0,Benchmark 定义七大错误域:

| 域 | 范围 | 说明 |
|----|------|------|
| 配置 | 1xxx | 配置文件加载/解析错误 |
| 算法 | 2xxx | 算法基准加载/执行错误 |
| 度量 | 3xxx | 度量收集/统计错误 |
| 运行 | 4xxx | 运行器/调度错误 |
| IO | 5xxx | 输入输出错误 |
| 报告 | 6xxx | 报告生成错误 |
| 系统 | 7xxx | 系统级错误 |

## 工程标准

- 遵循 SpharxTools 39 项 ACC 验收标准(适配版)
- 覆盖率 ≥ 85%
- Python 3.11+
- 参考文档: `docs/DEVELOPMENT_GUIDE.md`

## License

GPL-3.0-or-later,见 [LICENSE](LICENSE)。
