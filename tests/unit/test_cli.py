# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_cli — CLI 入口与示例基准测试"""

import json
import os

import pytest

from core_benchmark.cli import main, run_suite
from core_benchmark.cli.demo_benchmarks import (
    SortBenchmark,
    SumBenchmark,
    HashBenchmark,
    get_demo_benchmarks,
)
from core_benchmark.cli.main import _load_benchmarks, _parse_input, _build_parser
from core_benchmark.core.interfaces import IBenchmark


# =============================================================================
# 示例基准测试
# =============================================================================

class TestDemoBenchmarks:
    """内置示例基准测试"""

    def test_sort_benchmark(self):
        bench = SortBenchmark()
        assert bench.name == "sort"
        assert bench.version == "1.0.0"
        bench.setup()
        result = bench.run(100)
        assert isinstance(result, list)
        assert len(result) == 1000
        bench.teardown()

    def test_sum_benchmark(self):
        bench = SumBenchmark()
        assert bench.name == "sum"
        assert bench.version == "1.0.0"
        bench.setup()
        result = bench.run(100)
        assert result == sum(range(10000))
        bench.teardown()

    def test_hash_benchmark(self):
        bench = HashBenchmark()
        assert bench.name == "hash"
        assert bench.version == "1.0.0"
        bench.setup()
        result = bench.run("test_data")
        assert isinstance(result, str)
        assert len(result) > 0
        bench.teardown()

    def test_get_demo_benchmarks(self):
        benchmarks = get_demo_benchmarks()
        assert len(benchmarks) == 3
        for b in benchmarks:
            assert isinstance(b, IBenchmark)

    def test_benchmarks_implement_interface(self):
        for cls in [SortBenchmark, SumBenchmark, HashBenchmark]:
            assert issubclass(cls, IBenchmark)

    def test_setup_with_config(self):
        bench = SortBenchmark()
        bench.setup({"size": 500})
        assert bench._size == 500

        bench2 = SumBenchmark()
        bench2.setup({"n": 100})
        assert bench2._n == 100

        bench3 = HashBenchmark()
        bench3.setup({"hash_iterations": 50})
        assert bench3._iterations == 50

    def test_description_property(self):
        for bench in get_demo_benchmarks():
            assert hasattr(bench, "description")
            assert isinstance(bench.description, str)


# =============================================================================
# CLI 子命令测试
# =============================================================================

class TestCliInfo:
    """info 子命令测试"""

    def test_info_returns_zero(self, capsys):
        rc = main(["info"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Benchmark Library" in out
        assert "1.0.0" in out

    def test_info_shows_reporters(self, capsys):
        main(["info"])
        out = capsys.readouterr().out
        assert "json" in out
        assert "csv" in out
        assert "markdown" in out

    def test_info_shows_demo_benchmarks(self, capsys):
        main(["info"])
        out = capsys.readouterr().out
        assert "sort" in out
        assert "sum" in out
        assert "hash" in out


class TestCliConfig:
    """config 子命令测试"""

    def test_config_returns_zero(self, capsys):
        rc = main(["config"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "iterations" in out
        assert "warmup" in out
        assert "default_format" in out


class TestCliNoCommand:
    """无子命令测试"""

    def test_no_command_returns_zero(self, capsys):
        rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "usage:" in out.lower() or "benchmark" in out


# =============================================================================
# CLI run 子命令测试
# =============================================================================

class TestCliRun:
    """run 子命令测试"""

    def test_run_demo_stdout(self, capsys):
        rc = main(["run", "--demo", "--iterations", "5", "--warmup", "1", "--format", "json"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[INFO]" in out
        # JSON 输出应在 stdout 中
        assert "summary" in out

    def test_run_demo_file_output(self, tmp_path, capsys):
        out_file = tmp_path / "report.json"
        rc = main([
            "run", "--demo", "--iterations", "5",
            "--format", "json", "--output", str(out_file),
        ])
        assert rc == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["summary"]["total"] == 3

    def test_run_demo_parallel(self, capsys):
        rc = main([
            "run", "--demo", "--iterations", "3", "--warmup", "1",
            "--parallel", "--max-workers", "2",
            "--format", "csv",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "benchmark_name" in out

    def test_run_demo_markdown(self, capsys):
        rc = main(["run", "--demo", "--iterations", "3", "--format", "markdown"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "# Benchmark Report" in out

    def test_run_no_source_error(self, capsys):
        rc = main(["run", "--iterations", "5"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "ERROR" in err

    def test_run_with_suite_name(self, capsys):
        rc = main([
            "run", "--demo", "--iterations", "3",
            "--suite-name", "my_suite", "--format", "json",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        # 套件名不直接输出到 stdout,验证运行成功即可
        assert "[INFO] 完成" in out

    def test_run_with_input_expr(self, capsys):
        rc = main([
            "run", "--demo", "--iterations", "3",
            "--input-expr", "50", "--format", "json",
        ])
        assert rc == 0

    def test_run_with_config_file(self, tmp_path, capsys):
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("benchmark:\n  iterations: 3\n", encoding="utf-8")
        rc = main([
            "run", "--demo", "--config", str(config_yaml),
            "--format", "json",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "迭代 3 次" in out

    def test_run_load_benchmarks_from_module(self, capsys):
        rc = main([
            "run",
            "--benchmarks", "core_benchmark.cli.demo_benchmarks:SortBenchmark",
            "--iterations", "3",
            "--format", "json",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "1 个基准" in out


# =============================================================================
# 辅助函数测试
# =============================================================================

class TestHelperFunctions:
    """CLI 辅助函数测试"""

    def test_load_benchmarks_valid(self):
        benchmarks = _load_benchmarks("core_benchmark.cli.demo_benchmarks:SortBenchmark,SumBenchmark")
        assert len(benchmarks) == 2
        assert isinstance(benchmarks[0], SortBenchmark)
        assert isinstance(benchmarks[1], SumBenchmark)

    def test_load_benchmarks_no_colon(self):
        with pytest.raises(ValueError):
            _load_benchmarks("core_benchmark.cli.demo_benchmarks")

    def test_load_benchmarks_invalid_module(self):
        with pytest.raises(ImportError):
            _load_benchmarks("nonexistent_module:SomeClass")

    def test_load_benchmarks_invalid_class(self):
        with pytest.raises(AttributeError):
            _load_benchmarks("core_benchmark.cli.demo_benchmarks:NonexistentClass")

    def test_parse_input_default(self):
        assert _parse_input(None) == 100

    def test_parse_input_int(self):
        assert _parse_input("42") == 42

    def test_parse_input_list(self):
        result = _parse_input("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_parse_input_string_fallback(self):
        # 无效表达式应返回原始字符串
        result = _parse_input("hello world")
        assert result == "hello world"

    def test_build_parser(self):
        parser = _build_parser()
        assert parser is not None


# =============================================================================
# run_suite 入口测试
# =============================================================================

class TestRunSuite:
    """run_suite 脚本入口测试"""

    def test_run_suite_with_demo(self, capsys, monkeypatch):
        monkeypatch.setattr("sys.argv", ["benchmark-run", "--demo", "--iterations", "3", "--format", "json"])
        rc = run_suite()
        assert rc == 0
