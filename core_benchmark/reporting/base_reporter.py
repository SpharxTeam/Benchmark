# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.reporting.base_reporter — 报告生成器基类

提供 IReporter 接口的模板方法实现:
    - generate(): 通用流程(输入归一化 → 校验 → 渲染 → 输出)
    - _render(): 子类实现的渲染逻辑(抽象)

子类只需实现:
    - format 属性(报告格式标识)
    - _render() 方法(渲染报告内容字符串)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Union

from core_benchmark.core.abstractions import ErrorCode, ReportError
from core_benchmark.core.interfaces import IReporter
from core_benchmark.core.models import BenchmarkResult, SuiteResult

# 输入类型:结果列表 / 套件结果 / 单个结果
ReportInput = Union[
    List[BenchmarkResult],
    SuiteResult,
    BenchmarkResult,
]


class BaseReporter(IReporter):
    """
    报告生成器基类 — 模板方法模式

    实现 generate() 的通用流程:
        1. 归一化输入(接受 List/BenchmarkResult/SuiteResult)
        2. 校验输入非空
        3. 调用 _render() 渲染内容(子类实现)
        4. 写入文件或返回字符串

    子类必须实现:
        - format: 报告格式标识(str)
        - _render(results): 渲染报告内容(str)
    """

    def generate(
        self,
        results: ReportInput,
        output_path: Optional[str] = None,
    ) -> str:
        """
        生成报告

        Args:
            results: 基准测试结果(支持 List[BenchmarkResult] / SuiteResult / 单个 BenchmarkResult)
            output_path: 输出文件路径(None 表示返回字符串)

        Returns:
            报告内容字符串(output_path 为 None)或写入的文件路径

        Raises:
            ReportError: 输入为空 / 渲染失败 / 文件写入失败
        """
        # 1. 归一化输入
        normalized = self._normalize_input(results)

        # 2. 校验非空
        if not normalized:
            raise ReportError(
                code=ErrorCode.REPORT_INVALID_DATA,
                message="报告生成失败: 结果列表为空",
                report_format=self.format,
            )

        # 3. 渲染内容
        try:
            content = self._render(normalized)
        except ReportError:
            raise
        except Exception as e:
            raise ReportError(
                code=ErrorCode.REPORT_RENDER_ERROR,
                message=f"报告渲染失败: {e}",
                report_format=self.format,
            ) from e

        # 4. 输出
        if output_path is None:
            return content

        return self._write_file(content, output_path)

    def _normalize_input(
        self, results: ReportInput
    ) -> List[BenchmarkResult]:
        """
        归一化输入为 BenchmarkResult 列表

        支持的输入类型:
            - List[BenchmarkResult]: 直接返回
            - SuiteResult: 提取 .results
            - BenchmarkResult: 包装为单元素列表
        """
        if isinstance(results, SuiteResult):
            return list(results.results)
        if isinstance(results, BenchmarkResult):
            return [results]
        if isinstance(results, list):
            return list(results)
        # 兜底:尝试转为列表
        return [results]  # type: ignore[list-item]

    def _render(self, results: List[BenchmarkResult]) -> str:
        """
        渲染报告内容 — 子类必须实现

        Args:
            results: 归一化后的基准结果列表

        Returns:
            报告内容字符串
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} 必须实现 _render() 方法"
        )

    def _write_file(self, content: str, output_path: str) -> str:
        """
        将内容写入文件

        自动创建不存在的父目录。

        Args:
            content: 报告内容
            output_path: 目标文件路径

        Returns:
            写入的文件路径(绝对路径)

        Raises:
            ReportError: 文件写入失败
        """
        path = Path(output_path)

        # 创建父目录
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ReportError(
                code=ErrorCode.REPORT_OUTPUT_ERROR,
                message=f"无法创建输出目录 {path.parent}: {e}",
                report_format=self.format,
            ) from e

        # 写入文件
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as e:
            raise ReportError(
                code=ErrorCode.REPORT_OUTPUT_ERROR,
                message=f"无法写入报告文件 {path}: {e}",
                report_format=self.format,
            ) from e

        return str(path.resolve())


__all__ = ["BaseReporter", "ReportInput"]
