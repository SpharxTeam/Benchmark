# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.cli.main — 命令行入口

提供 Benchmark 库的命令行界面:
    - benchmark run: 运行基准测试(支持 --demo 或自定义模块)
    - benchmark info: 显示版本与报告格式信息
    - benchmark config: 显示默认配置

子命令:
    run    运行基准测试套件
    info   显示库信息
    config 显示/导出默认配置

使用示例:
    # 运行内置示例基准
    benchmark run --demo --iterations 100 --format json --output ./report.json

    # 运行自定义基准
    benchmark run --benchmarks my_module:MyBench1,MyBench2 --iterations 50

    # 显示默认配置
    benchmark config --show

    # 显示库信息
    benchmark info
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, List, Optional

from core_benchmark.core.abstractions import BenchmarkError
from core_benchmark.core.interfaces import IBenchmark
from core_benchmark.config import load_config, get_default_config
from core_benchmark.metrics import MemoryCollector
from core_benchmark.reporting import CsvReporter, JsonReporter, MarkdownReporter
from core_benchmark.runners import BenchmarkSuiteRunner

from core_benchmark.cli.demo_benchmarks import get_demo_benchmarks


# =============================================================================
# 常量
# =============================================================================

_VERSION = "1.0.0"
_REPORTERS = {
    "json": JsonReporter,
    "csv": CsvReporter,
    "markdown": MarkdownReporter,
}


# =============================================================================
# 子命令实现
# =============================================================================

def _cmd_run(args: argparse.Namespace) -> int:
    """执行 run 子命令"""
    # 1. 加载配置
    try:
        config = load_config(args.config) if args.config else get_default_config()
    except BenchmarkError as e:
        print(f"[ERROR] 配置加载失败: {e}", file=sys.stderr)
        return 1

    # 2. 加载基准
    benchmarks: List[IBenchmark] = []
    if args.demo:
        benchmarks = get_demo_benchmarks()
    elif args.benchmarks:
        try:
            benchmarks = _load_benchmarks(args.benchmarks)
        except (ImportError, AttributeError, ValueError) as e:
            print(f"[ERROR] 基准加载失败: {e}", file=sys.stderr)
            return 1
    else:
        print(
            "[ERROR] 必须指定 --demo 或 --benchmarks <module:Class1,Class2>",
            file=sys.stderr,
        )
        return 1

    if not benchmarks:
        print("[ERROR] 未加载到任何基准", file=sys.stderr)
        return 1

    # 3. 解析参数(命令行覆盖配置)
    iterations = args.iterations if args.iterations is not None else config.benchmark.iterations
    warmup = args.warmup if args.warmup is not None else config.benchmark.warmup
    parallel = args.parallel if args.parallel is not None else config.benchmark.parallel
    max_workers = args.max_workers if args.max_workers is not None else config.benchmark.max_workers

    # 4. 解析输入数据
    input_data = _parse_input(args.input_expr)

    # 5. 注册并运行
    suite = BenchmarkSuiteRunner(suite_name=args.suite_name or "cli_suite")
    for bench in benchmarks:
        suite.register(bench.name, bench, collectors=[MemoryCollector()])

    try:
        print(f"[INFO] 运行 {suite.size} 个基准,迭代 {iterations} 次,预热 {warmup} 次...")
        result = suite.run_all(
            input_data=input_data,
            iterations=iterations,
            warmup=warmup,
            parallel=parallel,
            max_workers=max_workers,
        )
    except BenchmarkError as e:
        print(f"[ERROR] 基准执行失败: {e}", file=sys.stderr)
        return 1

    # 6. 输出结果
    print(f"[INFO] 完成: {result.success_count}/{result.total_count} 成功, "
          f"耗时 {result.total_duration_seconds:.4f}s")

    fmt = args.format or config.reporting.default_format
    reporter_cls = _REPORTERS.get(fmt)
    if reporter_cls is None:
        print(f"[ERROR] 不支持的报告格式: {fmt}", file=sys.stderr)
        return 1

    reporter = reporter_cls()

    if args.output:
        try:
            path = reporter.generate(result, args.output)
            print(f"[INFO] 报告已写入: {path}")
        except BenchmarkError as e:
            print(f"[ERROR] 报告生成失败: {e}", file=sys.stderr)
            return 1
    else:
        content = reporter.generate(result)
        print("\n" + "=" * 60)
        print(content)

    return 0 if result.failure_count == 0 else 1


def _cmd_info(args: argparse.Namespace) -> int:
    """执行 info 子命令"""
    print(f"Benchmark Library v{_VERSION}")
    print(f"Copyright (c) 2026 SPHARX. All Rights Reserved.")
    print(f'"\u4ece\u6570\u636e\u667a\u80fd\u4e2d\u6d8c\u73b0" "From data intelligence emerges"')
    print()
    print("支持的报告格式:")
    for fmt, cls in _REPORTERS.items():
        print(f"  - {fmt}: {cls.__name__}")
    print()
    print("内置示例基准 (--demo):")
    for bench in get_demo_benchmarks():
        desc = getattr(bench, "description", "")
        print(f"  - {bench.name} v{bench.version}: {desc}")
    return 0


def _cmd_config(args: argparse.Namespace) -> int:
    """执行 config 子命令"""
    config = get_default_config()
    print("# Benchmark 默认配置")
    print(f"benchmark:")
    print(f"  iterations: {config.benchmark.iterations}")
    print(f"  warmup: {config.benchmark.warmup}")
    print(f"  parallel: {config.benchmark.parallel}")
    print(f"  max_workers: {config.benchmark.max_workers}")
    print()
    print(f"reporting:")
    print(f"  output_dir: {config.reporting.output_dir}")
    print(f"  default_format: {config.reporting.default_format}")
    print(f"  include_metadata: {config.reporting.include_metadata}")
    print()
    print(f"logging:")
    print(f"  level: {config.logging.level}")
    return 0


# =============================================================================
# 辅助函数
# =============================================================================

def _load_benchmarks(spec: str) -> List[IBenchmark]:
    """
    从模块加载基准类

    格式: module:Class1,Class2  或  module.path:Class1,Class2

    Args:
        spec: 模块和类名规范

    Returns:
        基准实例列表

    Raises:
        ValueError: 格式错误
        ImportError: 模块不存在
        AttributeError: 类不存在
    """
    if ":" not in spec:
        raise ValueError(
            f"基准规范格式错误,应为 'module:Class1,Class2',实际为 '{spec}'"
        )
    module_path, class_names = spec.split(":", 1)
    module = importlib.import_module(module_path)

    benchmarks: List[IBenchmark] = []
    for cls_name in class_names.split(","):
        cls_name = cls_name.strip()
        if not cls_name:
            continue
        cls = getattr(module, cls_name)
        benchmarks.append(cls())
    return benchmarks


def _parse_input(expr: Optional[str]) -> Any:
    """
    解析输入数据表达式

    Args:
        expr: Python 表达式字符串(如 "100", "[1,2,3]", "'hello'")

    Returns:
        解析后的值(默认 100)
    """
    if expr is None:
        return 100
    try:
        return eval(expr, {"__builtins__": {}}, {})  # noqa: S307
    except Exception:
        # 解析失败,返回原始字符串
        return expr


# =============================================================================
# 主入口
# =============================================================================

def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="benchmark",
        description="Benchmark - 独立算法基准库 v" + _VERSION,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # --- run 子命令 ---
    run_parser = subparsers.add_parser(
        "run", help="运行基准测试套件"
    )
    run_parser.add_argument(
        "--demo", action="store_true",
        help="使用内置示例基准",
    )
    run_parser.add_argument(
        "--benchmarks", type=str, default=None,
        help="自定义基准: module:Class1,Class2",
    )
    run_parser.add_argument(
        "--config", type=str, default=None,
        help="配置文件路径(默认使用内置配置)",
    )
    run_parser.add_argument(
        "--iterations", type=int, default=None,
        help="正式迭代次数(覆盖配置)",
    )
    run_parser.add_argument(
        "--warmup", type=int, default=None,
        help="预热迭代次数(覆盖配置)",
    )
    run_parser.add_argument(
        "--parallel", action="store_true", default=None,
        help="并行执行多算法基准",
    )
    run_parser.add_argument(
        "--max-workers", type=int, default=None,
        help="并行最大线程数",
    )
    run_parser.add_argument(
        "--format", choices=list(_REPORTERS.keys()), default=None,
        help="报告格式(默认使用配置中的 default_format)",
    )
    run_parser.add_argument(
        "--output", type=str, default=None,
        help="报告输出路径(不指定则打印到 stdout)",
    )
    run_parser.add_argument(
        "--input-expr", type=str, default=None,
        help="输入数据 Python 表达式(如 100, [1,2,3], 'text')",
    )
    run_parser.add_argument(
        "--suite-name", type=str, default=None,
        help="套件名称(默认 cli_suite)",
    )

    # --- info 子命令 ---
    subparsers.add_parser("info", help="显示库信息")

    # --- config 子命令 ---
    subparsers.add_parser("config", help="显示默认配置")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    主 CLI 入口

    Args:
        argv: 命令行参数列表(None 表示从 sys.argv 读取)

    Returns:
        退出码(0 成功, 1 失败)
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        return _cmd_run(args)
    elif args.command == "info":
        return _cmd_info(args)
    elif args.command == "config":
        return _cmd_config(args)

    parser.print_help()
    return 0


def run_suite() -> int:
    """
    benchmark-run 脚本入口

    等价于 `benchmark run`,将参数直接传递给 run 子命令。
    """
    # 如果第一个参数不是已知子命令,插入 "run"
    known_commands = {"run", "info", "config", "-h", "--help"}
    argv = sys.argv[1:]
    if argv and argv[0] not in known_commands:
        argv = ["run"] + argv
    return main(argv)


__all__ = ["main", "run_suite"]
