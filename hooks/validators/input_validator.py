"""Layer 1: 输入验证 — 规范化预处理 + 注入检测"""
import re
import urllib.parse
from validators.base import BaseValidator
from core.models import HookInput, ValidationResult

# 预编译正则缓存
_COMPILED = {}


def _compile(pattern):
    if pattern not in _COMPILED:
        _COMPILED[pattern] = re.compile(pattern, re.IGNORECASE)
    return _COMPILED[pattern]


class InputValidator(BaseValidator):
    """Layer 1: 输入验证层"""

    @property
    def layer_name(self):
        return "input_validation"

    def validate(self, hook_input: HookInput) -> ValidationResult:
        tool = hook_input.tool_name
        params = hook_input.tool_input

        # 对 Bash 命令进行输入验证
        if tool == "Bash":
            cmd = params.get("command", "")
            normalized = self._normalize(cmd)
            result = self._check_command_injection(normalized)
            if result:
                return result

        # 对文件操作进行路径验证
        if tool in ("Write", "Edit", "Read"):
            file_path = params.get("file_path", "")
            normalized_path = self._normalize(file_path)
            result = self._check_path_traversal(normalized_path)
            if result:
                return result

        return ValidationResult(passed=True, layer=self.layer_name)

    def _normalize(self, text: str) -> str:
        """规范化预处理：URL解码、Unicode规范化、去除零宽字符"""
        # URL 解码（防止 %2e%2e%2f 绕过）
        try:
            text = urllib.parse.unquote(text)
        except Exception:
            pass
        # 去除零宽字符
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        return text

    def _check_command_injection(self, cmd: str) -> ValidationResult | None:
        """检测命令注入"""
        injection_patterns = [
            (r'\$\([^)]+\)', "Command substitution $()"),
            (r'`[^`]+`', "Backtick command execution"),
            (r';\s*\w+', "Command chaining with semicolon"),
            (r'\|\s*\w+', "Pipe to another command"),
            (r'&&|\|\|', "Logical operator chaining"),
            (r'>\s*/dev/', "Redirect to device file"),
            (r'\$\{[^}]+\}', "Variable expansion"),
            # 新增：高级绕过检测
            (r'\$\\\(', "Escaped command substitution"),
            (r'\\x[0-9a-f]{2}', "Hex-encoded characters"),
            (r'base64\s+(--)?decode', "Base64 decode execution"),
            (r'curl\s+.*\|\s*(ba)?sh', "Curl pipe to shell"),
            (r'wget\s+.*-O\s*-\s*\|', "Wget pipe to command"),
            (r'python[23]?\s+-c\s+', "Python inline execution"),
            (r'perl\s+-e\s+', "Perl inline execution"),
            (r'ruby\s+-e\s+', "Ruby inline execution"),
            (r'nc\s+-[elp]', "Netcat listener/connection"),
            (r'ncat\s+', "Ncat connection"),
            (r'mkfifo\s+', "Named pipe creation"),
            (r'/dev/tcp/', "Bash TCP device"),
        ]
        for pattern, desc in injection_patterns:
            if _compile(pattern).search(cmd):
                return ValidationResult(
                    passed=False,
                    layer=self.layer_name,
                    severity="high",
                    reason=f"Command injection detected: {desc}",
                    violation_type="command_injection",
                )
        return None

    def _check_path_traversal(self, path: str) -> ValidationResult | None:
        """检测路径穿越"""
        traversal_patterns = [
            (r'\.\.[/\\]', "Parent directory traversal"),
            (r'^\s*[A-Z]:\\Windows\\System32', "Windows system directory"),
            (r'^\s*[A-Z]:\\Windows\\SysWOW64', "Windows SysWOW64"),
            (r'^/(etc|sys|proc|dev)/', "Linux system directory"),
            (r'%2e%2e[/\\%]', "URL-encoded traversal"),
            (r'\.\.\\|\.\./', "Directory traversal variant"),
            (r'\\\\[^\\]+\\', "UNC path access"),
        ]
        for pattern, desc in traversal_patterns:
            if _compile(pattern).search(path):
                return ValidationResult(
                    passed=False,
                    layer=self.layer_name,
                    severity="high",
                    reason=f"Path traversal detected: {desc}",
                    violation_type="path_traversal",
                )
        return None
