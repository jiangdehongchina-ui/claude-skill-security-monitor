"""数据模型定义"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HookInput:
    """Hook 输入数据"""
    session_id: str
    tool_name: str
    tool_input: dict
    cwd: str = ""
    hook_event_name: str = ""


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    layer: str = ""
    severity: str = ""
    reason: str = ""
    details: Optional[dict] = None
    violation_type: str = ""
