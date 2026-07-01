# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""string_benchmark — 字符串操作基准

对比三种字符串构建方式的性能:
    - StringConcatBenchmark: + 拼接 O(n²)
    - StringJoinBenchmark: str.join() O(n)
    - StringBufferBenchmark: io.StringIO 缓冲区 O(n)

使用示例:
    from examples.string_benchmark import StringConcatBenchmark, StringJoinBenchmark, StringBufferBenchmark
    from core_benchmark.runners import BenchmarkSuiteRunner

    suite = BenchmarkSuiteRunner("string_compare")
    suite.register("concat", StringConcatBenchmark())
    suite.register("join", StringJoinBenchmark())
    suite.register("buffer", StringBufferBenchmark())
    result = suite.run_all(input_data=500, iterations=100, warmup=5)
"""

from __future__ import annotations

from io import StringIO
from typing import Any

from core_benchmark.core.interfaces import IBenchmark


class StringConcatBenchmark(IBenchmark):
    """字符串拼接基准 — 使用 + 操作符 O(n²)"""

    @property
    def name(self) -> str:
        return "string_concat"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "字符串 + 拼接 O(n²) — 每次拼接创建新字符串"

    def setup(self, config: Any = None) -> None:
        self._count = 500
        if config and isinstance(config, dict):
            self._count = config.get("count", 500)

    def run(self, input_data: Any) -> str:
        result = ""
        for i in range(self._count):
            result += f"item_{i},"
        return result

    def teardown(self) -> None:
        pass


class StringJoinBenchmark(IBenchmark):
    """字符串 join 基准 — 使用 str.join() O(n)"""

    @property
    def name(self) -> str:
        return "string_join"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "str.join() O(n) — 一次性拼接列表中的字符串"

    def setup(self, config: Any = None) -> None:
        self._count = 500
        if config and isinstance(config, dict):
            self._count = config.get("count", 500)

    def run(self, input_data: Any) -> str:
        parts = [f"item_{i}" for i in range(self._count)]
        return ",".join(parts)

    def teardown(self) -> None:
        pass


class StringBufferBenchmark(IBenchmark):
    """StringIO 缓冲区基准 — 使用 io.StringIO O(n)"""

    @property
    def name(self) -> str:
        return "string_buffer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "io.StringIO O(n) — 可变字符串缓冲区"

    def setup(self, config: Any = None) -> None:
        self._count = 500
        if config and isinstance(config, dict):
            self._count = config.get("count", 500)

    def run(self, input_data: Any) -> str:
        buf = StringIO()
        for i in range(self._count):
            buf.write(f"item_{i},")
        return buf.getvalue()

    def teardown(self) -> None:
        pass


__all__ = [
    "StringConcatBenchmark",
    "StringJoinBenchmark",
    "StringBufferBenchmark",
]
