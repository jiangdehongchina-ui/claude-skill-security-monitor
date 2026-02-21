"""Layer 5: 审计日志 — 事件记录 + 日志轮转"""
import json
from pathlib import Path
from datetime import datetime, timezone
from validators.base import BaseValidator
from core.models import HookInput, ValidationResult

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "security_events.jsonl"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB


class AuditLogger(BaseValidator):
    """Layer 5: 审计日志层 — 始终通过，仅记录事件"""

    @property
    def layer_name(self):
        return "audit_log"

    def validate(self, hook_input: HookInput) -> ValidationResult:
        # 审计层不拦截，只记录
        return ValidationResult(passed=True, layer=self.layer_name)

    @staticmethod
    def log_event(session_id, tool_name, decision, reason,
                  details=None, execution_time=0, severity="",
                  violation_type=""):
        """记录安全事件到 JSONL 日志"""
        LOG_DIR.mkdir(exist_ok=True)

        # 日志轮转
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            archive = LOG_DIR / f"security_events_{ts}.jsonl"
            LOG_FILE.rename(archive)

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "tool_name": tool_name,
            "decision": decision,
            "reason": reason,
            "execution_time_ms": round(execution_time, 2),
        }
        if severity:
            event["severity"] = severity
        if violation_type:
            event["violation_type"] = violation_type
        if details:
            event["details"] = details

        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass  # 日志失败不应阻止执行
