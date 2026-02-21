"""Layer 3: 模式检测 — 基于正则的安全模式匹配"""
import re
from validators.base import BaseValidator
from core.models import HookInput, ValidationResult

_COMPILED = {}


def _compile(pattern):
    if pattern not in _COMPILED:
        _COMPILED[pattern] = re.compile(pattern, re.IGNORECASE)
    return _COMPILED[pattern]


class PatternDetector(BaseValidator):
    """Layer 3: 模式检测层"""

    @property
    def layer_name(self):
        return "pattern_detection"

    def validate(self, hook_input: HookInput) -> ValidationResult:
        tool = hook_input.tool_name
        params = hook_input.tool_input
        patterns = self.config.get("patterns", {})

        # 收集需要扫描的文本
        texts_to_scan = []
        if tool == "Bash":
            texts_to_scan.append(params.get("command", ""))
        elif tool in ("Write", "Edit"):
            texts_to_scan.append(params.get("content", ""))
            texts_to_scan.append(params.get("new_string", ""))
        elif tool == "Read":
            texts_to_scan.append(params.get("file_path", ""))

        # 对每段文本执行模式检测
        for text in texts_to_scan:
            if not text:
                continue
            result = self._scan_patterns(text, patterns)
            if result:
                return result

        return ValidationResult(passed=True, layer=self.layer_name)

    def _scan_patterns(self, text: str, patterns: dict) -> ValidationResult | None:
        """扫描文本中的危险模式"""
        for category, rules in patterns.items():
            if not isinstance(rules, list):
                continue
            for rule in rules:
                pattern = rule.get("pattern", "")
                severity = rule.get("severity", "medium")
                desc = rule.get("description", category)

                if not pattern:
                    continue

                try:
                    if _compile(pattern).search(text):
                        if severity in ("critical", "high"):
                            return ValidationResult(
                                passed=False,
                                layer=self.layer_name,
                                severity=severity,
                                reason=f"{category}: {desc}",
                                violation_type=category,
                            )
                except re.error:
                    continue
        return None
