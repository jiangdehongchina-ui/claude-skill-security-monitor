#!/usr/bin/env python3
"""
Claude Code Skill Security Monitor - Main Hook Script
修正版本：基于审查报告的所有P0/P1问题修正
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
import urllib.parse
import time

# 全局缓存：预编译的正则表达式
_COMPILED_PATTERNS = {}

def get_compiled_pattern(pattern_str):
    """获取预编译的正则表达式（带缓存）"""
    if pattern_str not in _COMPILED_PATTERNS:
        _COMPILED_PATTERNS[pattern_str] = re.compile(pattern_str, re.IGNORECASE)
    return _COMPILED_PATTERNS[pattern_str]

def read_hook_input():
    """修正：从stdin读取JSON，不是sys.argv"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse stdin: {e}")
        sys.exit(2)  # fail-closed

def main():
    start_time = time.time()  # 性能监控
    hook_data = read_hook_input()

    # 修正：使用正确的字段名
    session_id = hook_data.get("session_id", "unknown")
    tool_name = hook_data.get("tool_name")  # 不是"tool"
    tool_input = hook_data.get("tool_input")  # 不是"params"
    cwd = hook_data.get("cwd")

    if not tool_name or not tool_input:
        log_error("Missing tool_name or tool_input")
        sys.exit(2)

    # 加载配置
    try:
        config = load_config()
        whitelist = load_whitelist()
    except Exception as e:
        log_error(f"Failed to load config: {e}")
        sys.exit(2)  # fail-closed

    # 检查白名单
    if is_whitelisted(tool_name, tool_input, whitelist):
        execution_time = (time.time() - start_time) * 1000
        log_event(session_id, tool_name, "allow", "whitelisted", execution_time=execution_time)
        sys.exit(0)

    # Layer 1: Input Validation
    result = validate_input(tool_name, tool_input, config)
    if not result["safe"]:
        execution_time = (time.time() - start_time) * 1000
        handle_violation(session_id, tool_name, tool_input, result, execution_time)
        sys.exit(2)

    # Layer 2: Permission Check
    result = check_permission(tool_name, tool_input, config)
    if not result["allowed"]:
        execution_time = (time.time() - start_time) * 1000
        handle_violation(session_id, tool_name, tool_input, result, execution_time)
        sys.exit(2)

    # Layer 3: Pattern Detection
    result = detect_patterns(tool_name, tool_input, config)
    if result["risk_level"] in ["critical", "high"]:
        execution_time = (time.time() - start_time) * 1000
        handle_violation(session_id, tool_name, tool_input, result, execution_time)
        sys.exit(2)

    # Layer 4: Content Scan
    if tool_name in ["Write", "Edit"]:
        content = tool_input.get("content") or tool_input.get("new_string", "")
        if content:
            result = scan_content(content, config)
            if not result["safe"]:
                execution_time = (time.time() - start_time) * 1000
                handle_violation(session_id, tool_name, tool_input, result, execution_time)
                sys.exit(2)

    # Layer 5: Audit Log
    execution_time = (time.time() - start_time) * 1000
    log_event(session_id, tool_name, "allow", "passed all checks", execution_time=execution_time)
    sys.exit(0)

def validate_input(tool_name, tool_input, config):
    """Layer 1: 输入验证"""
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        normalized = normalize_command(command)

        patterns = config.get("patterns", {}).get("command_injection", [])
        for p in patterns:
            compiled_pattern = get_compiled_pattern(p["pattern"])
            if compiled_pattern.search(normalized):
                return {
                    "safe": False,
                    "reason": f"Command injection: {p['description']}",
                    "severity": p["severity"]
                }

    elif tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path", "")

        # 路径穿越检测
        if ".." in file_path:
            return {
                "safe": False,
                "reason": "Path traversal detected",
                "severity": "high"
            }

        # 系统路径检测
        if is_blocked_path(file_path, config):
            return {
                "safe": False,
                "reason": f"Blocked path: {file_path}",
                "severity": "critical"
            }

    return {"safe": True}

def check_permission(tool_name, tool_input, config):
    """Layer 2: 权限检查"""
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        cmd_parts = command.split()
        if not cmd_parts:
            return {"allowed": False, "reason": "Empty command", "severity": "low"}

        base_cmd = cmd_parts[0]
        allowed_cmds = config.get("permissions", {}).get("allowed_commands", {})

        if base_cmd not in allowed_cmds:
            return {
                "allowed": False,
                "reason": f"Command '{base_cmd}' not in whitelist",
                "severity": "medium"
            }

    return {"allowed": True}

def detect_patterns(tool_name, tool_input, config):
    """Layer 3: 模式检测"""
    risk_level = "low"
    reason = ""

    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # 危险命令检测
        dangerous_cmds = ["rm -rf", "dd if=", "mkfs", "format", ":(){:|:&};:"]
        for cmd in dangerous_cmds:
            if cmd in command:
                return {
                    "risk_level": "critical",
                    "reason": f"Dangerous command detected: {cmd}"
                }

        # 网络命令检测
        if any(x in command for x in ["curl", "wget", "nc", "netcat"]):
            if any(x in command for x in ["http://", "https://", "ftp://"]):
                risk_level = "medium"
                reason = "Network request detected"

    return {"risk_level": risk_level, "reason": reason}

def scan_content(content, config):
    """Layer 4: 内容扫描（改进版，减少误报）"""
    patterns = config.get("patterns", {})

    # 检测凭证（增加上下文检查）
    for p in patterns.get("credentials", []):
        compiled_pattern = get_compiled_pattern(p["pattern"])
        matches = compiled_pattern.finditer(content)

        for match in matches:
            matched_text = match.group(0)

            # 减少误报：检查是否在注释中
            start_pos = max(0, match.start() - 50)
            context = content[start_pos:match.start()]

            # 跳过注释中的匹配
            if any(marker in context for marker in ["#", "//", "/*", "<!--"]):
                continue

            # 跳过示例代码和文档
            if any(keyword in context.lower() for keyword in ["example", "sample", "test", "demo", "placeholder"]):
                continue

            # 跳过明显的测试凭证
            if any(test_val in matched_text.lower() for test_val in ["test", "fake", "dummy", "example", "xxx", "000"]):
                continue

            return {
                "safe": False,
                "reason": f"Credential detected: {p['description']}",
                "severity": p["severity"],
                "matched": matched_text[:50]  # 只显示前50个字符
            }

    # 检测危险代码
    for p in patterns.get("dangerous_code", []):
        compiled_pattern = get_compiled_pattern(p["pattern"])
        if compiled_pattern.search(content):
            return {
                "safe": False,
                "reason": f"Dangerous code: {p['description']}",
                "severity": p["severity"]
            }

    return {"safe": True}

def handle_violation(session_id, tool_name, tool_input, result, execution_time=0):
    """处理安全违规（警告并询问用户）"""
    log_event(session_id, tool_name, "deny", result.get("reason", "Security violation"), result, execution_time=execution_time)

    # 显示警告信息到stderr
    severity = result.get("severity", "high")
    reason = result.get("reason", "Security violation detected")

    warning = f"""
╔══════════════════════════════════════════════════════════╗
║       SECURITY WARNING - Skill Monitor                  ║
╠══════════════════════════════════════════════════════════╣
║ Tool: {tool_name}
║ Severity: {severity.upper()}
║ Reason: {reason}
║
║ This operation has been BLOCKED for security reasons.
║
║ To allow this operation:
║ 1. Review the details above carefully
║ 2. If you trust this operation, add to whitelist:
║    python hooks/whitelist_manager.py add
║ 3. Re-run the command
╚══════════════════════════════════════════════════════════╝
"""
    print(warning, file=sys.stderr)

def normalize_command(command):
    """规范化命令（防止绕过）"""
    # URL解码
    decoded = urllib.parse.unquote(command)
    # 移除多余空白
    normalized = " ".join(decoded.split())
    return normalized

def is_blocked_path(file_path, config):
    """检查路径是否被阻止"""
    blocked_paths = config.get("permissions", {}).get("blocked_paths", [])

    for pattern in blocked_paths:
        # 简单的通配符匹配
        if "**" in pattern:
            prefix = pattern.replace("**", "")
            if file_path.startswith(prefix):
                return True
        elif pattern in file_path:
            return True

    return False

def load_config():
    """加载配置文件"""
    config_dir = Path(__file__).parent / "config"

    config = {}

    # 加载permissions.yaml
    permissions_file = config_dir / "permissions.yaml"
    if permissions_file.exists():
        try:
            import yaml
            with open(permissions_file, encoding="utf-8") as f:
                config["permissions"] = yaml.safe_load(f).get("permissions", {})
        except Exception as e:
            log_error(f"Failed to load permissions.yaml: {e}")

    # 加载patterns.yaml
    patterns_file = config_dir / "patterns.yaml"
    if patterns_file.exists():
        try:
            import yaml
            with open(patterns_file, encoding="utf-8") as f:
                config["patterns"] = yaml.safe_load(f)
        except Exception as e:
            log_error(f"Failed to load patterns.yaml: {e}")

    return config

def load_whitelist():
    """加载白名单"""
    whitelist_file = Path(__file__).parent / "config" / "whitelist.json"
    if whitelist_file.exists():
        try:
            with open(whitelist_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log_error(f"Failed to load whitelist.json: {e}")

    return {"version": "1.0", "entries": []}

def is_whitelisted(tool_name, tool_input, whitelist):
    """检查是否在白名单中"""
    for entry in whitelist.get("entries", []):
        if entry.get("tool") == tool_name:
            # 简单匹配：检查关键字段
            if "command" in entry and "command" in tool_input:
                if entry["command"] == tool_input["command"]:
                    return True
            elif "file_path" in entry and "file_path" in tool_input:
                if entry["file_path"] == tool_input["file_path"]:
                    return True

    return False

def log_event(session_id, tool_name, decision, reason, details=None, **kwargs):
    """Layer 5: 审计日志（带日志轮转）"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "security_events.jsonl"

    # 日志轮转：如果文件超过10MB，重命名并创建新文件
    if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:
        # 重命名为带时间戳的文件
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_file = log_dir / f"security_events_{timestamp}.jsonl"
        log_file.rename(archive_file)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "tool_name": tool_name,
        "decision": decision,
        "reason": reason,
        "execution_time_ms": kwargs.get("execution_time", 0)
    }

    if details:
        event["details"] = details

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        # 日志失败不应阻止执行
        print(f"Warning: Failed to write log: {e}", file=sys.stderr)

def log_error(message):
    """记录错误到stderr"""
    print(f"ERROR: {message}", file=sys.stderr)

if __name__ == "__main__":
    main()
