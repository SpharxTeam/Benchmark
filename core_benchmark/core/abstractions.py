# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.core.abstractions — ErrorCode 与异常体系

Benchmark 独立算法基准库的统一错误码体系,参考 Workshop WS-T01 ErrorCode v4.0。

七大错误域:
    - 1xxx: 配置域 (Configuration)
    - 2xxx: 算法域 (Algorithm)
    - 3xxx: 度量域 (Metric)
    - 4xxx: 运行域 (Runner)
    - 5xxx: IO 域 (Input/Output)
    - 6xxx: 报告域 (Reporting)
    - 7xxx: 系统域 (System)

设计原则:
    1. 覆盖七大域,每域 1000 个码值,便于扩展
    2. SUCCESS=0 表示成功
    3. IntEnum 实现,支持数值比较与序列化
    4. ErrorSeverity 含兼容别名 (LOW=WARNING, MEDIUM=ERROR, HIGH=CRITICAL)
    5. 异常类按域分类,携带上下文信息

参考:
    - Workshop WS-T01 ErrorCode v4.0 (core_workshop/core/abstractions/models.py)
    - SpharxTools 工程标准规范手册
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional, Union


# =============================================================================
# 第四套统一 ErrorCode 体系 (Benchmark 适配版)
# =============================================================================

class ErrorCode(IntEnum):
    """
    Benchmark 统一错误码枚举 - v1.0

    覆盖七大域,千位分段:
        - 1xxx: 配置域 (Configuration)
        - 2xxx: 算法域 (Algorithm)
        - 3xxx: 度量域 (Metric)
        - 4xxx: 运行域 (Runner)
        - 5xxx: IO 域 (Input/Output)
        - 6xxx: 报告域 (Reporting)
        - 7xxx: 系统域 (System)

    兼容性:
        - 与 Workshop ErrorCode v4.0 设计对齐(工程标准统一)
        - 错误码语义化命名,便于诊断
    """

    SUCCESS = 0

    # === 1xxx: 配置域 (Configuration) ===
    CONFIG_NOT_FOUND = 1001
    CONFIG_PARSE_ERROR = 1002
    CONFIG_MISSING_REQUIRED = 1003
    CONFIG_INVALID_FORMAT = 1004
    CONFIG_FILE_NOT_FOUND = 1005
    CONFIG_VALIDATION_ERROR = 1006
    CONFIG_TYPE_ERROR = 1007

    # === 2xxx: 算法域 (Algorithm) ===
    ALGORITHM_NOT_FOUND = 2001
    ALGORITHM_LOAD_FAILED = 2002
    ALGORITHM_EXECUTION_FAILED = 2003
    ALGORITHM_INIT_FAILED = 2004
    ALGORITHM_INVALID_INPUT = 2005
    ALGORITHM_TIMEOUT = 2006
    ALGORITHM_NOT_REGISTERED = 2007
    ALGORITHM_DEPENDENCY_MISSING = 2008

    # === 3xxx: 度量域 (Metric) ===
    METRIC_COLLECTION_FAILED = 3001
    METRIC_INVALID_TYPE = 3002
    METRIC_CALCULATION_ERROR = 3003
    METRIC_NOT_SUPPORTED = 3004
    METRIC_INSUFFICIENT_SAMPLES = 3005
    METRIC_PERCENTILE_ERROR = 3006
    METRIC_OUT_OF_RANGE = 3007

    # === 4xxx: 运行域 (Runner) ===
    RUNNER_INIT_FAILED = 4001
    RUNNER_EXECUTION_FAILED = 4002
    RUNNER_NOT_CONFIGURED = 4003
    RUNNER_SUITE_EMPTY = 4004
    RUNNER_PARALLEL_ERROR = 4005
    RUNNER_TIMEOUT = 4006
    RUNNER_CANCELED = 4007
    RUNNER_INVALID_ITERATIONS = 4008

    # === 5xxx: IO 域 (Input/Output) ===
    IO_FILE_NOT_FOUND = 5001
    IO_PERMISSION_DENIED = 5002
    IO_READ_ERROR = 5003
    IO_WRITE_ERROR = 5004
    IO_DIRECTORY_NOT_FOUND = 5005
    IO_DISK_FULL = 5006
    IO_ENCODING_ERROR = 5007

    # === 6xxx: 报告域 (Reporting) ===
    REPORT_GENERATION_FAILED = 6001
    REPORT_FORMAT_NOT_SUPPORTED = 6002
    REPORT_TEMPLATE_ERROR = 6003
    REPORT_OUTPUT_ERROR = 6004
    REPORT_INVALID_DATA = 6005
    REPORT_RENDER_ERROR = 6006

    # === 7xxx: 系统域 (System) ===
    UNKNOWN_ERROR = 7000
    OPERATION_TIMEOUT = 7001
    RESOURCE_UNAVAILABLE = 7002
    OUT_OF_MEMORY = 7003
    NOT_IMPLEMENTED = 7004
    INTERNAL_ERROR = 7005
    CANCELED = 7006

    @property
    def code(self) -> int:
        """错误码数字(兼容调用方式 `ErrorCode.X.code`)"""
        return int(self)

    @property
    def message(self) -> str:
        """错误码中文描述"""
        return _ERROR_MESSAGES.get(int(self), "未知错误")

    @property
    def domain(self) -> str:
        """错误码所属域"""
        domain_prefix = int(self) // 1000
        return _DOMAIN_MAP.get(domain_prefix, "Unknown")

    def __str__(self) -> str:
        return f"[{int(self)}] {self.message}"


# =============================================================================
# 域名映射表
# =============================================================================

_DOMAIN_MAP: Dict[int, str] = {
    0: "Success",
    1: "Configuration",
    2: "Algorithm",
    3: "Metric",
    4: "Runner",
    5: "IO",
    6: "Reporting",
    7: "System",
}


# =============================================================================
# 错误码中文描述映射表
# =============================================================================

_ERROR_MESSAGES: Dict[int, str] = {
    # 通用
    0: "成功",

    # 1xxx: 配置域
    1001: "配置不存在",
    1002: "配置解析错误",
    1003: "配置缺少必需项",
    1004: "配置格式无效",
    1005: "配置文件未找到",
    1006: "配置验证失败",
    1007: "配置类型错误",

    # 2xxx: 算法域
    2001: "算法未找到",
    2002: "算法加载失败",
    2003: "算法执行失败",
    2004: "算法初始化失败",
    2005: "算法输入无效",
    2006: "算法执行超时",
    2007: "算法未注册",
    2008: "算法依赖缺失",

    # 3xxx: 度量域
    3001: "度量收集失败",
    3002: "度量类型无效",
    3003: "度量计算错误",
    3004: "度量不支持",
    3005: "度量样本不足",
    3006: "百分位计算错误",
    3007: "度量值超出范围",

    # 4xxx: 运行域
    4001: "运行器初始化失败",
    4002: "运行器执行失败",
    4003: "运行器未配置",
    4004: "基准套件为空",
    4005: "并行执行错误",
    4006: "运行器超时",
    4007: "运行已取消",
    4008: "迭代次数无效",

    # 5xxx: IO 域
    5001: "文件未找到",
    5002: "权限拒绝",
    5003: "文件读取错误",
    5004: "文件写入错误",
    5005: "目录不存在",
    5006: "磁盘空间不足",
    5007: "编码错误",

    # 6xxx: 报告域
    6001: "报告生成失败",
    6002: "报告格式不支持",
    6003: "报告模板错误",
    6004: "报告输出错误",
    6005: "报告数据无效",
    6006: "报告渲染错误",

    # 7xxx: 系统域
    7000: "未知错误",
    7001: "操作超时",
    7002: "资源不可用",
    7003: "内存不足",
    7004: "未实现",
    7005: "内部错误",
    7006: "操作已取消",
}


# =============================================================================
# ErrorSeverity - 错误严重级别
# =============================================================================

class ErrorSeverity(IntEnum):
    """
    错误严重级别 - IntEnum 实现

    主流值:
        - DEBUG = 0
        - INFO = 1
        - WARNING = 2
        - ERROR = 3
        - CRITICAL = 4
        - FATAL = 5

    兼容别名(与 Workshop/Deepness 对齐):
        - LOW = WARNING (2)
        - MEDIUM = ERROR (3)
        - HIGH = CRITICAL (4)
    """

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    FATAL = 5

    # 兼容别名(与 Workshop/Deepness 历史代码对齐)
    LOW = WARNING       # LOW = 2
    MEDIUM = ERROR      # MEDIUM = 3
    HIGH = CRITICAL     # HIGH = 4

    @property
    def label(self) -> str:
        """严重级别中文标签"""
        return _SEVERITY_LABELS.get(int(self), "未知")

    def should_retry(self) -> bool:
        """
        判断该严重级别是否建议重试

        Returns:
            bool: WARNING 及以下建议重试,ERROR 及以上不建议重试
        """
        return int(self) <= int(ErrorSeverity.WARNING)

    def __str__(self) -> str:
        return self.name


_SEVERITY_LABELS: Dict[int, str] = {
    0: "调试",
    1: "信息",
    2: "警告",
    3: "错误",
    4: "严重",
    5: "致命",
}


# =============================================================================
# ErrorContext - 错误上下文
# =============================================================================

@dataclass
class ErrorContext:
    """
    错误上下文 - 记录错误发生时的环境信息

    用于在错误传播链中携带诊断信息,支持错误追溯和调试。
    """

    timestamp: datetime = field(default_factory=datetime.now)
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "stack_trace": self.stack_trace,
            "additional_info": self.additional_info,
        }


# =============================================================================
# BenchmarkError - 基础异常类
# =============================================================================

class BenchmarkError(Exception):
    """
    Benchmark 基础异常类

    所有 Benchmark 异常的基类,提供统一的错误信息格式、上下文携带和序列化能力。

    Attributes:
        code: 错误码 (ErrorCode 枚举)
        message: 错误消息(默认使用错误码消息)
        severity: 严重级别 (ErrorSeverity 枚举)
        cause: 原始异常(可选)
        context: 错误上下文 (ErrorContext)

    Example:
        >>> raise AlgorithmError(
        ...     code=ErrorCode.ALGORITHM_EXECUTION_FAILED,
        ...     message="排序算法执行失败",
        ...     algorithm_name="quick_sort"
        ... )
    """

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化异常

        Args:
            code: 错误码
            message: 错误消息(默认使用错误码消息)
            severity: 严重级别
            cause: 原始异常
            context: 上下文信息
        """
        self._code = code
        self._severity = severity
        self._cause = cause
        self._context = ErrorContext(additional_info=context or {})

        # 设置消息
        self._message = message or code.message

        # 获取调用栈信息
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            self._context.module = frame.f_back.f_globals.get("__name__")
            self._context.function = frame.f_back.f_code.co_name
            self._context.line_number = frame.f_back.f_lineno

        # 获取堆栈跟踪
        if cause:
            self._context.stack_trace = "".join(
                traceback.format_exception(type(cause), cause, cause.__traceback__)
            )

        super().__init__(str(self))

    @property
    def code(self) -> ErrorCode:
        return self._code

    @property
    def severity(self) -> ErrorSeverity:
        return self._severity

    @property
    def message(self) -> str:
        return self._message

    @property
    def cause(self) -> Optional[Exception]:
        return self._cause

    @property
    def context(self) -> ErrorContext:
        return self._context

    def to_dict(self, include_stack_trace: bool = False) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            include_stack_trace: 是否包含堆栈跟踪

        Returns:
            Dict: 字典表示
        """
        result: Dict[str, Any] = {
            "error": True,
            "code": self._code.code,
            "code_name": self._code.name,
            "message": self._message,
            "severity": self._severity.name,
            "domain": self._code.domain,
            "context": self._context.to_dict(),
        }

        if include_stack_trace and self._context.stack_trace:
            result["stack_trace"] = self._context.stack_trace

        if self._cause:
            result["cause"] = str(self._cause)

        return result

    def __str__(self) -> str:
        return f"[{self._code.code}] {self._message}"

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"code={self._code.name} "
            f"severity={self._severity.name}>"
        )


# =============================================================================
# 具体异常类 - 按域分类
# =============================================================================

class ConfigurationError(BenchmarkError):
    """配置错误 - 1xxx 域"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.CONFIG_PARSE_ERROR,
        message: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if config_key:
            context["config_key"] = config_key
        super().__init__(code, message, context=context, **kwargs)


class AlgorithmError(BenchmarkError):
    """算法错误 - 2xxx 域"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.ALGORITHM_EXECUTION_FAILED,
        message: Optional[str] = None,
        algorithm_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if algorithm_name:
            context["algorithm_name"] = algorithm_name
        super().__init__(code, message, context=context, **kwargs)


class MetricError(BenchmarkError):
    """度量错误 - 3xxx 域"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.METRIC_CALCULATION_ERROR,
        message: Optional[str] = None,
        metric_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if metric_name:
            context["metric_name"] = metric_name
        super().__init__(code, message, context=context, **kwargs)


class RunnerError(BenchmarkError):
    """运行器错误 - 4xxx 域"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.RUNNER_EXECUTION_FAILED,
        message: Optional[str] = None,
        runner_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if runner_name:
            context["runner_name"] = runner_name
        super().__init__(code, message, context=context, **kwargs)


class BenchmarkIOError(BenchmarkError):
    """
    数据 IO 错误 - 5xxx 域

    注意: 命名为 BenchmarkIOError 以避免遮蔽 Python 内置 IOError
    (参考 Deepness DN-B02 教训: 避免遮蔽内置异常)
    """

    def __init__(
        self,
        code: ErrorCode = ErrorCode.IO_READ_ERROR,
        message: Optional[str] = None,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation
        super().__init__(code, message, context=context, **kwargs)


class ReportError(BenchmarkError):
    """报告错误 - 6xxx 域"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.REPORT_GENERATION_FAILED,
        message: Optional[str] = None,
        report_format: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if report_format:
            context["report_format"] = report_format
        super().__init__(code, message, context=context, **kwargs)


class BenchmarkSystemError(BenchmarkError):
    """
    系统错误 - 7xxx 域

    注意: 命名为 BenchmarkSystemError 以避免遮蔽 Python 内置 SystemError
    (参考 Deepness DN-B02 教训: 避免遮蔽内置异常)
    """

    def __init__(
        self,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(code, message, **kwargs)


# =============================================================================
# ErrorCodeManager - 错误码管理器
# =============================================================================

class ErrorCodeManager:
    """
    错误码管理器

    提供错误码的注册、查询、统计、域名分类和重试判断功能。

    职责:
        1. 错误统计: 记录错误发生次数
        2. 错误历史: 保留最近 N 条错误
        3. 域名分类: 根据错误码判断所属域
        4. 重试判断: 根据错误码判断是否可重试
    """

    # 可重试错误码集合
    RETRIABLE_CODES: frozenset = frozenset({
        ErrorCode.OPERATION_TIMEOUT,
        ErrorCode.RUNNER_TIMEOUT,
        ErrorCode.ALGORITHM_TIMEOUT,
        ErrorCode.RESOURCE_UNAVAILABLE,
        ErrorCode.IO_DISK_FULL,
        ErrorCode.OUT_OF_MEMORY,
    })

    def __init__(self) -> None:
        self._error_stats: Dict[str, int] = {}
        self._error_history: List[BenchmarkError] = []
        self._max_history = 1000

    def record_error(self, error: BenchmarkError) -> None:
        """记录错误"""
        error_name = error.code.name
        self._error_stats[error_name] = self._error_stats.get(error_name, 0) + 1

        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            "total_errors": sum(self._error_stats.values()),
            "by_code": dict(self._error_stats),
            "unique_codes": len(self._error_stats),
        }

    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        return [error.to_dict() for error in self._error_history[-count:]]

    def clear_stats(self) -> None:
        """清除统计"""
        self._error_stats.clear()
        self._error_history.clear()

    def get_domain(self, code: ErrorCode) -> str:
        """获取错误码所属域"""
        return code.domain

    def is_retriable(self, code: ErrorCode) -> bool:
        """判断错误码是否可重试"""
        return code in self.RETRIABLE_CODES

    def get_all_error_codes(self) -> List[ErrorCode]:
        """获取所有已定义的错误码"""
        return list(ErrorCode)

    def get_codes_by_domain(self, domain_prefix: int) -> List[ErrorCode]:
        """获取指定域的所有错误码"""
        return [
            code for code in ErrorCode
            if int(code) // 1000 == domain_prefix
        ]


# 全局错误码管理器实例
error_code_manager = ErrorCodeManager()


__all__ = [
    # 错误码
    "ErrorCode",
    "ErrorSeverity",
    "ErrorContext",
    # 异常基类
    "BenchmarkError",
    # 具体异常(按域)
    "ConfigurationError",
    "AlgorithmError",
    "MetricError",
    "RunnerError",
    "BenchmarkIOError",
    "ReportError",
    "BenchmarkSystemError",
    # 管理器
    "ErrorCodeManager",
    "error_code_manager",
]
