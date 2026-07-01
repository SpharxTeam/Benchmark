# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_full_suite — 端到端集成测试

验证完整工作流:配置加载 → 基准注册 → 套件运行 → 度量收集 → 报告生成
"""

import csv
import io
import json
import os
import tempfile

import pytest

from core_benchmark.config import load_config, get_default_config
from core_benchmark.core.interfaces import IBenchmark
from core_benchmark.metrics import LatencyCollector, MemoryCollector, AccuracyCollector
from core_benchmark.reporting import JsonReporter, CsvReporter, MarkdownReporter
from core_benchmark.runners import BaseBenchmarkRunner, BenchmarkSuiteRunner


# =============================================================================
# 测试用基准
# =============================================================================

class FastBenchmark(IBenchmark):
    """快速基准(简单求和)"""
    @property
    def name(self): return "fast"
    @property
    def version(self): return "1.0.0"
    @property
    def description(self): return "快速求和基准"
    def setup(self, config=None): pass
    def run(self, input_data):
        return sum(range(input_data))
    def teardown(self): pass


class SlowBenchmark(IBenchmark):
    """慢速基准(嵌套循环)"""
    @property
    def name(self): return "slow"
    @property
    def version(self): return "1.0.0"
    @property
    def description(self): return "慢速嵌套循环基准"
    def setup(self, config=None): pass
    def run(self, input_data):
        total = 0
        for i in range(input_data):
            for j in range(10):
                total += i * j
        return total
    def teardown(self): pass


class FailingBenchmark(IBenchmark):
    """总是失败的基准(用于错误隔离测试)"""
    @property
    def name(self): return "failing"
    @property
    def version(self): return "1.0.0"
    def setup(self, config=None): pass
    def run(self, input_data):
        raise RuntimeError("故意失败")
    def teardown(self): pass


# =============================================================================
# 端到端集成测试
# =============================================================================

class TestFullWorkflow:
    """完整工作流集成测试"""

    def test_end_to_end_serial(self):
        """端到端串行流程:配置 → 注册 → 运行 → 报告"""
        # 1. 加载默认配置
        config = get_default_config()
        assert config.benchmark.iterations == 100

        # 2. 创建并注册基准
        suite = BenchmarkSuiteRunner("integration_suite")
        suite.register("fast", FastBenchmark(), collectors=[MemoryCollector()])
        suite.register("slow", SlowBenchmark())

        # 3. 运行套件(串行)
        result = suite.run_all(
            input_data=50,
            iterations=10,
            warmup=2,
        )

        # 4. 验证结果
        assert result.total_count == 2
        assert result.success_count == 2
        assert result.failure_count == 0
        assert result.success_rate == 1.0
        assert result.total_duration_seconds > 0

        # 5. 验证每个基准结果
        for r in result.results:
            assert r.success is True
            assert "latency" in r.metrics
            assert r.iterations == 10

        # 6. 生成 JSON 报告
        json_reporter = JsonReporter()
        json_content = json_reporter.generate(result)
        json_data = json.loads(json_content)
        assert json_data["summary"]["total"] == 2
        assert json_data["summary"]["success"] == 2

        # 7. 生成 CSV 报告
        csv_reporter = CsvReporter()
        csv_content = csv_reporter.generate(result)
        csv_rows = list(csv.reader(io.StringIO(csv_content)))
        assert len(csv_rows) == 3  # header + 2 data

        # 8. 生成 Markdown 报告
        md_reporter = MarkdownReporter(title="Integration Test")
        md_content = md_reporter.generate(result)
        assert "# Integration Test" in md_content
        assert "fast" in md_content
        assert "slow" in md_content

    def test_end_to_end_parallel(self):
        """端到端并行流程"""
        suite = BenchmarkSuiteRunner("parallel_suite")
        suite.register("fast", FastBenchmark())
        suite.register("slow", SlowBenchmark())

        result = suite.run_all(
            input_data=50,
            iterations=10,
            warmup=2,
            parallel=True,
            max_workers=2,
        )

        assert result.total_count == 2
        assert result.success_count == 2

    def test_end_to_end_with_file_output(self, tmp_path):
        """端到端文件输出流程"""
        suite = BenchmarkSuiteRunner("file_suite")
        suite.register("fast", FastBenchmark())
        result = suite.run_all(input_data=50, iterations=5)

        # 生成三种格式的报告文件
        json_path = tmp_path / "report.json"
        csv_path = tmp_path / "report.csv"
        md_path = tmp_path / "report.md"

        JsonReporter().generate(result, str(json_path))
        CsvReporter().generate(result, str(csv_path))
        MarkdownReporter().generate(result, str(md_path))

        # 验证文件存在且非空
        assert json_path.exists()
        assert csv_path.exists()
        assert md_path.exists()
        assert json_path.stat().st_size > 0
        assert csv_path.stat().st_size > 0
        assert md_path.stat().st_size > 0

        # 验证 JSON 文件可解析
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["summary"]["total"] == 1

    def test_error_isolation_in_suite(self):
        """套件中错误隔离:一个失败不影响其他"""
        suite = BenchmarkSuiteRunner("mixed_suite")
        suite.register("fast", FastBenchmark())
        suite.register("failing", FailingBenchmark())
        suite.register("slow", SlowBenchmark())

        result = suite.run_all(input_data=50, iterations=5)

        assert result.total_count == 3
        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.success_rate == pytest.approx(2.0 / 3.0)

        # 验证失败基准的结果
        failing_result = result.get_result("failing")
        assert failing_result is not None
        assert failing_result.success is False
        assert failing_result.error is not None

    def test_input_provider_callback(self):
        """InputProvider 回调:每个基准获取不同输入"""
        suite = BenchmarkSuiteRunner("callback_suite")
        suite.register("fast", FastBenchmark())
        suite.register("slow", SlowBenchmark())

        def provider(name):
            if name == "fast":
                return 100
            elif name == "slow":
                return 20
            return 50

        result = suite.run_all(input_data=provider, iterations=5)
        assert result.success_count == 2


# =============================================================================
# 配置驱动的集成测试
# =============================================================================

class TestConfigDrivenWorkflow:
    """配置驱动的集成测试"""

    def test_config_overrides_applied(self, tmp_path):
        """用户配置覆盖默认值"""
        config_yaml = tmp_path / "custom.yaml"
        config_yaml.write_text(
            "benchmark:\n"
            "  iterations: 5\n"
            "  warmup: 1\n"
            "  parallel: true\n"
            "  max_workers: 2\n"
            "reporting:\n"
            "  default_format: markdown\n",
            encoding="utf-8",
        )

        config = load_config(str(config_yaml))
        assert config.benchmark.iterations == 5
        assert config.benchmark.warmup == 1
        assert config.benchmark.parallel is True
        assert config.benchmark.max_workers == 2
        assert config.reporting.default_format == "markdown"

        # 使用配置参数运行基准
        suite = BenchmarkSuiteRunner("config_driven")
        suite.register("fast", FastBenchmark())
        result = suite.run_all(
            input_data=50,
            iterations=config.benchmark.iterations,
            warmup=config.benchmark.warmup,
            parallel=config.benchmark.parallel,
            max_workers=config.benchmark.max_workers,
        )
        assert result.success_count == 1
        assert result.results[0].iterations == 5


# =============================================================================
# 跨模块集成测试
# =============================================================================

class TestCrossModuleIntegration:
    """跨模块集成测试"""

    def test_base_runner_with_all_collectors(self):
        """BaseBenchmarkRunner 集成所有收集器"""
        bench = FastBenchmark()
        runner = BaseBenchmarkRunner(
            bench,
            collectors=[MemoryCollector(), AccuracyCollector()],
        )
        result = runner.run(input_data=100, iterations=10, warmup=2)

        assert result.success is True
        assert "latency" in result.metrics
        assert "memory" in result.metrics

    def test_full_pipeline_to_all_reports(self, tmp_path):
        """完整管道:运行 → 3种报告格式"""
        suite = BenchmarkSuiteRunner("pipeline_suite")
        suite.register("a", FastBenchmark())
        suite.register("b", SlowBenchmark())
        result = suite.run_all(input_data=30, iterations=5, warmup=1)

        # JSON
        json_str = JsonReporter().generate(result)
        data = json.loads(json_str)
        assert len(data["results"]) == 2
        for r in data["results"]:
            assert "latency" in r["metrics"]

        # CSV
        csv_str = CsvReporter().generate(result)
        rows = list(csv.reader(io.StringIO(csv_str)))
        assert len(rows) == 3

        # Markdown
        md_str = MarkdownReporter().generate(result)
        assert "汇总摘要" in md_str
        assert "详细结果" in md_str
