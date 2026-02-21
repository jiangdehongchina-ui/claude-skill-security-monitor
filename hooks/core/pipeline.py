"""SecurityPipeline — 五层安全检测管道"""
from .models import HookInput, ValidationResult


class SecurityPipeline:
    """按顺序执行五层安全检测"""

    def __init__(self, layers):
        self.layers = layers

    def execute(self, hook_input: HookInput) -> ValidationResult:
        """依次执行每层检测，任一层失败则立即返回"""
        for layer in self.layers:
            result = layer.validate(hook_input)
            if not result.passed:
                return result
        return ValidationResult(passed=True, layer="all", reason="All checks passed")
