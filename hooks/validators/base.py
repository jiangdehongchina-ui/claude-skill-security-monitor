"""BaseValidator — 验证器抽象基类"""
from abc import ABC, abstractmethod
from core.models import HookInput, ValidationResult


class BaseValidator(ABC):
    """所有安全检测层的基类"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def validate(self, hook_input: HookInput) -> ValidationResult:
        """执行验证，返回 ValidationResult"""
        pass

    @property
    @abstractmethod
    def layer_name(self) -> str:
        """层名称标识"""
        pass
