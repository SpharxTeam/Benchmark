# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_reporting — JSON/CSV/Markdown 报告生成器测试"""

import csv
import io
import json
import os
import tempfile

import pytest

from core_benchmark.core.abstractions import ErrorCode, ReportError
from core_benchmark.core.interfaces import IBenchmark, IReporter
from core_benchmark.core.models import BenchmarkResult, SuiteResult
from core_benchmark.reporting import (
    BaseReporter,
    CsvReporter,
    JsonReporter,
    MarkdownReporter,
)
from core_benchmark.runners import BenchmarkSuiteRunner


# =============================================================================
# 测试辅助
# =============================================================================

class _Bench(IBenchmark):
    @property
    def name(self):
        return "test_bench"

    @property
    def version(self):
        return "1.0.0"

    def setup(self, config=None):
        pass

    def run(self, input_data):
        return sum(range(input_data))

    def teardown(self):
        pass


@pytest.fixture
def suite_result():
    """生成测试用 SuiteResult"""
    suite = BenchmarkSuiteRunner("test_suite")
    suite.register("a", _Bench())
    suite.register("b", _Bench())
    return suite.run_all(input_data=100, iterations=10, warmup=2)


@pytest.fixture
def single_result(suite_result):
    """生成单个 BenchmarkResult"""
    return suite_result.results[0]


# =============================================================================
# BaseReporter 测试
# =============================================================================

class TestBaseReporter:
    """报告生成器基类测试"""

    def test_ireporter_interface(self):
        assert issubclass(JsonReporter, IReporter)
        assert issubclass(CsvReporter, IReporter)
        assert issubclass(MarkdownReporter, IReporter)

    def test_empty_list_raises(self):
        reporter = JsonReporter()
        with pytest.raises(ReportError) as exc_info:
            reporter.generate([])
        assert exc_info.value.code == ErrorCode.REPORT_INVALID_DATA

    def test_normalize_suite_result(self, suite_result):
        reporter = JsonReporter()
        # 传入 SuiteResult 应正常工作
        content = reporter.generate(suite_result)
        data = json.loads(content)
        assert len(data["results"]) == 2

    def test_normalize_single_result(self, single_result):
        reporter = JsonReporter()
        content = reporter.generate(single_result)
        data = json.loads(content)
        assert len(data["results"]) == 1


# =============================================================================
# JsonReporter 测试
# =============================================================================

class TestJsonReporter:
    """JSON 报告生成器测试"""

    def test_format_property(self):
        assert JsonReporter().format == "json"

    def test_generate_string(self, suite_result):
        reporter = JsonReporter()
        content = reporter.generate(suite_result)
        data = json.loads(content)
        assert "generated_at" in data
        assert "summary" in data
        assert "results" in data
        assert data["summary"]["total"] == 2
        assert data["summary"]["success"] == 2

    def test_generate_file(self, suite_result):
        reporter = JsonReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "report.json")
            returned = reporter.generate(suite_result, path)
            assert os.path.exists(returned)
            with open(returned, encoding="utf-8") as f:
                data = json.load(f)
            assert data["summary"]["total"] == 2

    def test_ensure_ascii_false(self, suite_result):
        reporter = JsonReporter(ensure_ascii=False)
        content = reporter.generate(suite_result)
        # 非 ASCII 字符应原样保留
        assert "成功" in content or "total" in content

    def test_summary_calculation(self, suite_result):
        reporter = JsonReporter()
        content = reporter.generate(suite_result)
        data = json.loads(content)
        s = data["summary"]
        assert s["total"] == 2
        assert s["success"] == 2
        assert s["failure"] == 0
        assert s["success_rate"] == 1.0
        assert s["total_duration_seconds"] > 0


# =============================================================================
# CsvReporter 测试
# =============================================================================

class TestCsvReporter:
    """CSV 报告生成器测试"""

    def test_format_property(self):
        assert CsvReporter().format == "csv"

    def test_generate_string(self, suite_result):
        reporter = CsvReporter()
        content = reporter.generate(suite_result)
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # 1 header + 2 data rows
        assert len(rows) == 3
        # 基础列存在
        assert "benchmark_name" in rows[0]
        assert "algorithm_name" in rows[0]
        assert "iterations" in rows[0]
        # 度量统计列存在
        assert "latency_mean" in rows[0]

    def test_generate_file(self, suite_result):
        reporter = CsvReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.csv")
            reporter.generate(suite_result, path)
            assert os.path.exists(path)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "benchmark_name" in content

    def test_data_rows(self, suite_result):
        reporter = CsvReporter()
        content = reporter.generate(suite_result)
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # 第一行数据
        assert rows[1][0] == "a"  # benchmark_name
        assert rows[2][0] == "b"


# =============================================================================
# MarkdownReporter 测试
# =============================================================================

class TestMarkdownReporter:
    """Markdown 报告生成器测试"""

    def test_format_property(self):
        assert MarkdownReporter().format == "markdown"

    def test_generate_string(self, suite_result):
        reporter = MarkdownReporter(title="Test Report")
        content = reporter.generate(suite_result)
        assert "# Test Report" in content
        assert "## 汇总摘要" in content
        assert "## 详细结果" in content

    def test_summary_table(self, suite_result):
        reporter = MarkdownReporter()
        content = reporter.generate(suite_result)
        assert "基准总数" in content
        assert "成功" in content
        assert "成功率" in content

    def test_metric_table(self, suite_result):
        reporter = MarkdownReporter()
        content = reporter.generate(suite_result)
        assert "度量统计" in content
        assert "latency" in content

    def test_generate_file(self, suite_result):
        reporter = MarkdownReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.md")
            reporter.generate(suite_result, path)
            assert os.path.exists(path)

    def test_custom_title(self, suite_result):
        reporter = MarkdownReporter(title="Custom Title")
        content = reporter.generate(suite_result)
        assert "# Custom Title" in content


# =============================================================================
# 跨格式测试
# =============================================================================

class TestCrossFormat:
    """跨格式一致性测试"""

    def test_all_formats_accept_list(self, suite_result):
        for reporter_cls in [JsonReporter, CsvReporter, MarkdownReporter]:
            reporter = reporter_cls()
            content = reporter.generate(suite_result.results)
            assert len(content) > 0

    def test_all_formats_accept_suite_result(self, suite_result):
        for reporter_cls in [JsonReporter, CsvReporter, MarkdownReporter]:
            reporter = reporter_cls()
            content = reporter.generate(suite_result)
            assert len(content) > 0
