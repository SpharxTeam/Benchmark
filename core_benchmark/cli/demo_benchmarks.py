# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.cli.demo_benchmarks — 内置示例基准

提供三个简单的 CPU 密集型基准,用于 --demo 模式和快速验证:
    - SortBenchmark: 列表排序
    - SumBenchmark: 数值求和
    - HashBenchmark: 字符串哈希

使用示例:
    python -m core_benchmark.cli.main run --demo --iterations 100
"""

from __future__ import annotations

import hashlib
from typing import Any

from core_benchmark.core.interfaces import IBenchmark


class SortBenchmark(IBenchmark):
    """列表排序基准 — 对给定大小的随机列表进行排序"""

    @property
    def name(self) -> str:
        return "sort"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "对列表进行排序(默认 1000 元素)"

    def setup(self, config: Any = None) -> None:
        self._size = 1000
        if config and isinstance(config, dict):
            self._size = config.get("size", 1000)

    def run(self, input_data: Any) -> Any:
        import random
        data = [random.randint(0, 10000) for _ in range(self._size)]
        return sorted(data)

    def teardown(self) -> None:
        pass


class SumBenchmark(IBenchmark):
    """数值求和基准 — 计算 0..N 的和"""

    @property
    def name(self) -> str:
        return "sum"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "计算 0..N 的累加和(默认 N=10000)"

    def setup(self, config: Any = None) -> None:
        self._n = 10000
        if config and isinstance(config, dict):
            self._n = config.get("n", 10000)

    def run(self, input_data: Any) -> int:
        total = 0
        for i in range(self._n):
            total += i
        return total

    def teardown(self) -> None:
        pass


class HashBenchmark(IBenchmark):
    """字符串哈希基准 — 对字符串进行 N 次 SHA-256 哈希"""

    @property
    def name(self) -> str:
        return "hash"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "对字符串进行 N 次 SHA-256 迭代哈希(默认 N=1000)"

    def setup(self, config: Any = None) -> None:
        self._iterations = 1000
        if config and isinstance(config, dict):
            self._iterations = config.get("hash_iterations", 1000)

    def run(self, input_data: Any) -> str:
        data = str(input_data).encode("utf-8") if input_data else b"benchmark"
        for _ in range(self._iterations):
            data = hashlib.sha256(data).digest()
        return data.hex()

    def teardown(self) -> None:
        pass


def get_demo_benchmarks() -> list:
    """获取所有内置示例基准实例"""
    return [SortBenchmark(), SumBenchmark(), HashBenchmark()]


__all__ = [
    "SortBenchmark",
    "SumBenchmark",
    "HashBenchmark",
    "get_demo_benchmarks",
]
