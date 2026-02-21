#!/usr/bin/env python3
"""
Claude Code Skill Security Monitor - Main Hook Script
v2.0: 模块化管道架构，五层安全检测
"""
import sys
import json
import time

# 将 hooks/ 目录加入 Python 路径
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.config_loader import load_config, load_whitelist
from core.models import HookInput, ValidationResult
from core.pipeline import SecurityPipeline
from validators.input_validator import InputValidator
from validators.permission_checker import PermissionChecker
from validators.pattern_detector import PatternDetector
from validators.content_scanner import ContentScanner
from validators.audit_logger import AuditLogger


def read_hook_input() -> dict:
    """从 stdin 读取 JSON（Claude Code hook 标准输入方式）"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Security Monitor: Failed to parse stdin: {e}", file=sys.stderr)
        sys.exit(2)  # fail-closed


def is_whitelisted(tool_name: str, tool_input: dict, whitelist: dict) -> bool:
    """检查操作是否在白名单中"""
    import fnmatch
    for entry in whitelist.get("entries", []):
        if entry.get("tool") == tool_name:
            pattern = entry.get("pattern", "")
            # 对 Bash 匹配命令，对文件操作匹配路径
            target = ""
            if tool_name == "Bash":
                target = tool_input.get("command", "")
            elif tool_name in ("Write", "Edit", "Read"):
                target = tool_input.get("file_path", "")
            if pattern and fnmatch.fnmatch(target, pattern):
                return True
    return False


def main():
    start_time = time.time()

    # 1. 读取输入
    hook_data = read_hook_input()
    session_id = hook_data.get("session_id", "unknown")
    tool_name = hook_data.get("tool_name")
    tool_input = hook_data.get("tool_input")
    cwd = hook_data.get("cwd", "")

    if not tool_name or not tool_input:
        print("Security Monitor: Missing tool_name or tool_input", file=sys.stderr)
        sys.exit(2)

    # 2. 加载配置（fail-closed）
    try:
        config = load_config()
        whitelist = load_whitelist()
    except Exception as e:
        print(f"Security Monitor: Config load failed: {e}", file=sys.stderr)
        sys.exit(2)

    # 3. 白名单快速放行
    if is_whitelisted(tool_name, tool_input, whitelist):
        elapsed = (time.time() - start_time) * 1000
        AuditLogger.log_event(session_id, tool_name, "allow", "whitelisted",
                              execution_time=elapsed)
        sys.exit(0)

    # 4. 构建并执行五层安全管道
    hook_input = HookInput(
        session_id=session_id,
        tool_name=tool_name,
        tool_input=tool_input,
        cwd=cwd,
    )

    pipeline = SecurityPipeline([
        InputValidator(config),
        PermissionChecker(config),
        PatternDetector(config),
        ContentScanner(config),
        AuditLogger(config),
    ])

    result = pipeline.execute(hook_input)
    elapsed = (time.time() - start_time) * 1000

    # 5. 处理结果
    # 构建 details 摘要（用于事后分析误报）
    details = {}
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        details["command"] = cmd[:200] + ("..." if len(cmd) > 200 else "")
    elif tool_name in ("Write", "Edit"):
        details["file_path"] = tool_input.get("file_path", "")

    if result.passed:
        AuditLogger.log_event(session_id, tool_name, "allow", result.reason,
                              execution_time=elapsed)
        sys.exit(0)
    else:
        AuditLogger.log_event(session_id, tool_name, "deny", result.reason,
                              severity=result.severity,
                              violation_type=result.violation_type,
                              details=details,
                              execution_time=elapsed)
        print(f"Security Monitor [{result.layer}]: {result.reason}",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
