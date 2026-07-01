# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_error_codes — ErrorCode / ErrorSeverity / 异常体系 / ErrorCodeManager 测试"""

import pytest

from core_benchmark.core.abstractions import (
    ErrorCode,
    ErrorSeverity,
    ErrorContext,
    BenchmarkError,
    ConfigurationError,
    AlgorithmError,
    MetricError,
    RunnerError,
    BenchmarkIOError,
    ReportError,
    BenchmarkSystemError,
    ErrorCodeManager,
    error_code_manager,
)


# =============================================================================
# ErrorCode 测试
# =============================================================================

class TestErrorCode:
    """ErrorCode 枚举测试"""

    def test_success_is_zero(self):
        assert ErrorCode.SUCCESS == 0

    def test_config_domain_range(self):
        codes = [ErrorCode.CONFIG_NOT_FOUND, ErrorCode.CONFIG_TYPE_ERROR]
        for c in codes:
            assert 1000 <= int(c) < 2000

    def test_algorithm_domain_range(self):
        codes = [ErrorCode.ALGORITHM_NOT_FOUND, ErrorCode.ALGORITHM_DEPENDENCY_MISSING]
        for c in codes:
            assert 2000 <= int(c) < 3000

    def test_metric_domain_range(self):
        for c in [ErrorCode.METRIC_COLLECTION_FAILED, ErrorCode.METRIC_OUT_OF_RANGE]:
            assert 3000 <= int(c) < 4000

    def test_runner_domain_range(self):
        for c in [ErrorCode.RUNNER_INIT_FAILED, ErrorCode.RUNNER_INVALID_ITERATIONS]:
            assert 4000 <= int(c) < 5000

    def test_io_domain_range(self):
        for c in [ErrorCode.IO_FILE_NOT_FOUND, ErrorCode.IO_ENCODING_ERROR]:
            assert 5000 <= int(c) < 6000

    def test_report_domain_range(self):
        for c in [ErrorCode.REPORT_GENERATION_FAILED, ErrorCode.REPORT_RENDER_ERROR]:
            assert 6000 <= int(c) < 7000

    def test_system_domain_range(self):
        for c in [ErrorCode.UNKNOWN_ERROR, ErrorCode.CANCELED]:
            assert 7000 <= int(c) < 8000

    def test_code_property(self):
        assert ErrorCode.CONFIG_NOT_FOUND.code == 1001
        assert ErrorCode.UNKNOWN_ERROR.code == 7000

    def test_message_property(self):
        assert ErrorCode.SUCCESS.message == "成功"
        assert ErrorCode.CONFIG_NOT_FOUND.message == "配置不存在"

    def test_domain_property(self):
        assert ErrorCode.CONFIG_NOT_FOUND.domain == "Configuration"
        assert ErrorCode.ALGORITHM_NOT_FOUND.domain == "Algorithm"
        assert ErrorCode.UNKNOWN_ERROR.domain == "System"
        assert ErrorCode.SUCCESS.domain == "Success"

    def test_str_representation(self):
        s = str(ErrorCode.CONFIG_NOT_FOUND)
        assert "1001" in s
        assert "配置不存在" in s


# =============================================================================
# ErrorSeverity 测试
# =============================================================================

class TestErrorSeverity:
    """ErrorSeverity 枚举测试"""

    def test_main_values(self):
        assert ErrorSeverity.DEBUG == 0
        assert ErrorSeverity.INFO == 1
        assert ErrorSeverity.WARNING == 2
        assert ErrorSeverity.ERROR == 3
        assert ErrorSeverity.CRITICAL == 4
        assert ErrorSeverity.FATAL == 5

    def test_compat_aliases(self):
        assert ErrorSeverity.LOW == ErrorSeverity.WARNING == 2
        assert ErrorSeverity.MEDIUM == ErrorSeverity.ERROR == 3
        assert ErrorSeverity.HIGH == ErrorSeverity.CRITICAL == 4

    def test_should_retry(self):
        assert ErrorSeverity.DEBUG.should_retry() is True
        assert ErrorSeverity.INFO.should_retry() is True
        assert ErrorSeverity.WARNING.should_retry() is True
        assert ErrorSeverity.ERROR.should_retry() is False
        assert ErrorSeverity.CRITICAL.should_retry() is False
        assert ErrorSeverity.FATAL.should_retry() is False

    def test_label_property(self):
        assert ErrorSeverity.DEBUG.label == "调试"
        assert ErrorSeverity.ERROR.label == "错误"
        assert ErrorSeverity.FATAL.label == "致命"

    def test_str(self):
        assert str(ErrorSeverity.WARNING) == "WARNING"


# =============================================================================
# ErrorContext 测试
# =============================================================================

class TestErrorContext:
    """ErrorContext 数据类测试"""

    def test_defaults(self):
        ctx = ErrorContext()
        assert ctx.module is None
        assert ctx.function is None
        assert ctx.line_number is None
        assert ctx.stack_trace is None
        assert ctx.additional_info == {}

    def test_to_dict(self):
        ctx = ErrorContext(module="test_mod", function="test_fn", line_number=42)
        d = ctx.to_dict()
        assert d["module"] == "test_mod"
        assert d["function"] == "test_fn"
        assert d["line_number"] == 42
        assert "timestamp" in d


# =============================================================================
# BenchmarkError 基类测试
# =============================================================================

class TestBenchmarkError:
    """BenchmarkError 基类测试"""

    def test_construction_with_defaults(self):
        err = BenchmarkError(ErrorCode.UNKNOWN_ERROR)
        assert err.code == ErrorCode.UNKNOWN_ERROR
        assert err.message == "未知错误"

    def test_construction_with_message(self):
        err = BenchmarkError(ErrorCode.CONFIG_NOT_FOUND, message="自定义消息")
        assert err.message == "自定义消息"

    def test_construction_with_severity(self):
        err = BenchmarkError(ErrorCode.UNKNOWN_ERROR, severity=ErrorSeverity.CRITICAL)
        assert err.severity == ErrorSeverity.CRITICAL

    def test_construction_with_cause(self):
        cause = ValueError("原始错误")
        err = BenchmarkError(ErrorCode.UNKNOWN_ERROR, cause=cause)
        assert err.cause is cause

    def test_to_dict(self):
        err = BenchmarkError(ErrorCode.CONFIG_NOT_FOUND, message="测试")
        d = err.to_dict()
        assert d["code"] == 1001
        assert d["code_name"] == "CONFIG_NOT_FOUND"
        assert d["message"] == "测试"
        assert d["severity"] == "ERROR"

    def test_str(self):
        err = BenchmarkError(ErrorCode.CONFIG_NOT_FOUND)
        assert "[1001]" in str(err)

    def test_repr(self):
        err = BenchmarkError(ErrorCode.CONFIG_NOT_FOUND)
        r = repr(err)
        assert "CONFIG_NOT_FOUND" in r

    def test_is_exception(self):
        err = BenchmarkError(ErrorCode.UNKNOWN_ERROR)
        assert isinstance(err, Exception)


# =============================================================================
# 异常子类测试
# =============================================================================

class TestExceptionSubclasses:
    """各域异常子类测试"""

    def test_configuration_error(self):
        err = ConfigurationError(
            code=ErrorCode.CONFIG_NOT_FOUND,
            message="配置缺失",
            config_key="db.host",
        )
        assert isinstance(err, BenchmarkError)
        assert err.code == ErrorCode.CONFIG_NOT_FOUND

    def test_algorithm_error(self):
        err = AlgorithmError(
            code=ErrorCode.ALGORITHM_EXECUTION_FAILED,
            message="算法失败",
            algorithm_name="quick_sort",
        )
        assert isinstance(err, BenchmarkError)
        assert err.code == ErrorCode.ALGORITHM_EXECUTION_FAILED

    def test_metric_error(self):
        err = MetricError(
            code=ErrorCode.METRIC_CALCULATION_ERROR,
            message="计算失败",
            metric_name="latency",
        )
        assert isinstance(err, BenchmarkError)

    def test_runner_error(self):
        err = RunnerError(
            code=ErrorCode.RUNNER_SUITE_EMPTY,
            message="套件为空",
            runner_name="my_suite",
        )
        assert isinstance(err, BenchmarkError)

    def test_io_error_not_shadowing_builtin(self):
        """BenchmarkIOError 不应遮蔽 Python 内置 IOError"""
        err = BenchmarkIOError(
            code=ErrorCode.IO_FILE_NOT_FOUND,
            message="文件未找到",
            file_path="/tmp/test",
            operation="read",
        )
        assert isinstance(err, BenchmarkError)
        assert IOError is not BenchmarkIOError  # 内置 IOError 仍存在

    def test_report_error(self):
        err = ReportError(
            code=ErrorCode.REPORT_GENERATION_FAILED,
            message="报告失败",
            report_format="json",
        )
        assert isinstance(err, BenchmarkError)

    def test_system_error_not_shadowing_builtin(self):
        """BenchmarkSystemError 不应遮蔽 Python 内置 SystemError"""
        err = BenchmarkSystemError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="系统错误",
        )
        assert isinstance(err, BenchmarkError)
        assert SystemError is not BenchmarkSystemError  # 内置 SystemError 仍存在

    def test_raise_and_catch(self):
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError(code=ErrorCode.CONFIG_NOT_FOUND, message="测试异常")
        assert exc_info.value.code == ErrorCode.CONFIG_NOT_FOUND


# =============================================================================
# ErrorCodeManager 测试
# =============================================================================

class TestErrorCodeManager:
    """ErrorCodeManager 测试"""

    def test_record_and_stats(self):
        mgr = ErrorCodeManager()
        err1 = ConfigurationError(code=ErrorCode.CONFIG_NOT_FOUND, message="e1")
        err2 = ConfigurationError(code=ErrorCode.CONFIG_NOT_FOUND, message="e2")
        err3 = AlgorithmError(code=ErrorCode.ALGORITHM_NOT_FOUND, message="e3")
        mgr.record_error(err1)
        mgr.record_error(err2)
        mgr.record_error(err3)

        stats = mgr.get_stats()
        assert stats["total_errors"] == 3
        assert stats["unique_codes"] == 2
        assert stats["by_code"]["CONFIG_NOT_FOUND"] == 2
        assert stats["by_code"]["ALGORITHM_NOT_FOUND"] == 1

    def test_recent_errors(self):
        mgr = ErrorCodeManager()
        for i in range(5):
            mgr.record_error(
                ConfigurationError(code=ErrorCode.CONFIG_NOT_FOUND, message=f"e{i}")
            )
        recent = mgr.get_recent_errors(3)
        assert len(recent) == 3

    def test_clear_stats(self):
        mgr = ErrorCodeManager()
        mgr.record_error(ConfigurationError(code=ErrorCode.CONFIG_NOT_FOUND))
        mgr.clear_stats()
        stats = mgr.get_stats()
        assert stats["total_errors"] == 0

    def test_is_retriable(self):
        mgr = ErrorCodeManager()
        assert mgr.is_retriable(ErrorCode.OPERATION_TIMEOUT) is True
        assert mgr.is_retriable(ErrorCode.RUNNER_TIMEOUT) is True
        assert mgr.is_retriable(ErrorCode.CONFIG_NOT_FOUND) is False

    def test_get_domain(self):
        mgr = ErrorCodeManager()
        assert mgr.get_domain(ErrorCode.CONFIG_NOT_FOUND) == "Configuration"
        assert mgr.get_domain(ErrorCode.UNKNOWN_ERROR) == "System"

    def test_get_all_error_codes(self):
        mgr = ErrorCodeManager()
        codes = mgr.get_all_error_codes()
        assert ErrorCode.SUCCESS in codes
        assert ErrorCode.CONFIG_NOT_FOUND in codes
        assert len(codes) > 40  # 至少 40+ 错误码

    def test_get_codes_by_domain(self):
        mgr = ErrorCodeManager()
        config_codes = mgr.get_codes_by_domain(1)
        assert all(1000 <= int(c) < 2000 for c in config_codes)
        assert ErrorCode.CONFIG_NOT_FOUND in config_codes

    def test_global_manager_exists(self):
        assert error_code_manager is not None
        assert isinstance(error_code_manager, ErrorCodeManager)
