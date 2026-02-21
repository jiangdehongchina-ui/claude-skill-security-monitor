"""Layer 2: 权限控制 — 命令白名单 + 路径黑名单"""
import fnmatch
from validators.base import BaseValidator
from core.models import HookInput, ValidationResult


class PermissionChecker(BaseValidator):
    """Layer 2: 权限控制层"""

    @property
    def layer_name(self):
        return "permission_control"

    def validate(self, hook_input: HookInput) -> ValidationResult:
        tool = hook_input.tool_name
        params = hook_input.tool_input
        perms = self.config.get("permissions", {})

        # Bash 命令权限检查
        if tool == "Bash":
            cmd = params.get("command", "").strip()
            if not self._is_command_allowed(cmd, perms):
                return ValidationResult(
                    passed=False,
                    layer=self.layer_name,
                    severity="high",
                    reason=f"Command not in whitelist: {cmd.split()[0] if cmd else 'empty'}",
                    violation_type="permission_denied",
                )

        # 文件路径黑名单检查
        if tool in ("Write", "Edit", "Read"):
            file_path = params.get("file_path", "")
            if self._is_path_blocked(file_path, perms):
                return ValidationResult(
                    passed=False,
                    layer=self.layer_name,
                    severity="high",
                    reason=f"Blocked path: {file_path}",
                    violation_type="path_blocked",
                )

        return ValidationResult(passed=True, layer=self.layer_name)

    def _is_command_allowed(self, cmd: str, perms: dict) -> bool:
        """检查命令是否在白名单中"""
        if not cmd:
            return False

        allowed = perms.get("allowed_commands", {})
        parts = cmd.split()
        base_cmd = parts[0]

        # 处理路径前缀（如 /usr/bin/git）
        if "/" in base_cmd or "\\" in base_cmd:
            base_cmd = base_cmd.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

        if base_cmd not in allowed:
            return False

        allowed_args = allowed[base_cmd]
        if "*" in allowed_args:
            return True

        # 检查子命令
        if len(parts) > 1:
            sub_cmd = parts[1]
            for pattern in allowed_args:
                if fnmatch.fnmatch(sub_cmd, pattern):
                    return True
            return False

        return True

    def _is_path_blocked(self, file_path: str, perms: dict) -> bool:
        """检查路径是否在黑名单中"""
        blocked = perms.get("blocked_paths", [])
        normalized = file_path.replace("\\", "/")

        for pattern in blocked:
            pattern_normalized = pattern.replace("\\", "/")
            if fnmatch.fnmatch(normalized, pattern_normalized):
                return True
            if fnmatch.fnmatch(normalized.lower(), pattern_normalized.lower()):
                return True
        return False
