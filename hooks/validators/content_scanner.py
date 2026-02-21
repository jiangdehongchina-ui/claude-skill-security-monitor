"""Layer 4: 内容扫描 — 凭证泄露 + 危险代码检测"""
import re
from validators.base import BaseValidator
from core.models import HookInput, ValidationResult

_COMPILED = {}


def _compile(pattern):
    if pattern not in _COMPILED:
        _COMPILED[pattern] = re.compile(pattern, re.IGNORECASE)
    return _COMPILED[pattern]


# 内置凭证检测模式（补充 patterns.yaml 之外的云服务凭证）
EXTRA_CREDENTIAL_PATTERNS = [
    (r'ghp_[A-Za-z0-9_]{36}', "GitHub personal access token"),
    (r'gho_[A-Za-z0-9_]{36}', "GitHub OAuth token"),
    (r'github_pat_[A-Za-z0-9_]{22,}', "GitHub fine-grained PAT"),
    (r'glpat-[A-Za-z0-9\-_]{20,}', "GitLab personal access token"),
    (r'sk-[A-Za-z0-9]{48,}', "OpenAI API key"),
    (r'sk-ant-[A-Za-z0-9\-_]{40,}', "Anthropic API key"),
    (r'xoxb-[0-9]{10,}-[A-Za-z0-9]{20,}', "Slack bot token"),
    (r'xoxp-[0-9]{10,}-[A-Za-z0-9]{20,}', "Slack user token"),
    (r'SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}', "SendGrid API key"),
    (r'AIza[A-Za-z0-9_\-]{35}', "Google API key"),
    (r'ya29\.[A-Za-z0-9_\-]+', "Google OAuth token"),
    (r'AZURE_[A-Z_]+=\S{20,}', "Azure credential"),
    (r'AccountKey=[A-Za-z0-9+/=]{40,}', "Azure storage key"),
    (r'mongodb(\+srv)?://[^:]+:[^@]+@', "MongoDB connection string"),
    (r'postgres://[^:]+:[^@]+@', "PostgreSQL connection string"),
    (r'mysql://[^:]+:[^@]+@', "MySQL connection string"),
]


class ContentScanner(BaseValidator):
    """Layer 4: 内容扫描层"""

    @property
    def layer_name(self):
        return "content_scan"

    def validate(self, hook_input: HookInput) -> ValidationResult:
        tool = hook_input.tool_name
        params = hook_input.tool_input

        # 只扫描写入类操作的内容
        content = ""
        if tool == "Write":
            content = params.get("content", "")
        elif tool == "Edit":
            content = params.get("new_string", "")
        elif tool == "Bash":
            content = params.get("command", "")

        if not content:
            return ValidationResult(passed=True, layer=self.layer_name)

        # 扫描额外的凭证模式
        result = self._scan_credentials(content)
        if result:
            return result

        # 扫描数据外传行为
        result = self._scan_data_exfiltration(content, tool)
        if result:
            return result

        return ValidationResult(passed=True, layer=self.layer_name)

    def _scan_credentials(self, content: str) -> ValidationResult | None:
        """扫描凭证泄露"""
        for pattern, desc in EXTRA_CREDENTIAL_PATTERNS:
            if _compile(pattern).search(content):
                return ValidationResult(
                    passed=False,
                    layer=self.layer_name,
                    severity="critical",
                    reason=f"Credential exposure: {desc}",
                    violation_type="credential_exposure",
                )
        return None

    def _scan_data_exfiltration(self, content: str, tool: str) -> ValidationResult | None:
        """检测数据外传行为"""
        if tool != "Bash":
            return None

        exfil_patterns = [
            (r'curl\s+.*--data.*@', "Curl uploading file content"),
            (r'curl\s+.*-F\s+.*@', "Curl form file upload"),
            (r'wget\s+.*--post-file', "Wget POST file"),
            (r'scp\s+.*@.*:', "SCP file transfer"),
            (r'rsync\s+.*@.*:', "Rsync remote transfer"),
            (r'ftp\s+', "FTP connection"),
            (r'sftp\s+', "SFTP connection"),
        ]
        for pattern, desc in exfil_patterns:
            if _compile(pattern).search(content):
                return ValidationResult(
                    passed=False,
                    layer=self.layer_name,
                    severity="high",
                    reason=f"Potential data exfiltration: {desc}",
                    violation_type="data_exfiltration",
                )
        return None
