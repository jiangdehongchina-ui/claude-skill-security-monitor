#!/usr/bin/env python3
"""
PostToolUse Hook - 验证Write/Edit操作的结果
"""
import sys
import json
from pathlib import Path
from datetime import datetime

def read_hook_input():
    """从stdin读取JSON"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing stdin: {e}", file=sys.stderr)
        sys.exit(0)  # PostToolUse不阻止，只记录

def main():
    hook_data = read_hook_input()

    session_id = hook_data.get("session_id", "unknown")
    tool_name = hook_data.get("tool_name")
    tool_input = hook_data.get("tool_input")
    tool_output = hook_data.get("tool_output", {})

    if tool_name not in ["Write", "Edit"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")

    # 验证文件是否真的被写入
    if file_path and Path(file_path).exists():
        file_size = Path(file_path).stat().st_size

        # 记录写入操作
        log_event(session_id, tool_name, file_path, file_size)

        # 检查是否写入了敏感文件
        if is_sensitive_file(file_path):
            print(f"WARNING: Sensitive file written: {file_path}", file=sys.stderr)

    sys.exit(0)

def is_sensitive_file(file_path):
    """检查是否是敏感文件"""
    sensitive_patterns = [".env", "secret", "password", ".ssh", "id_rsa", ".pem", ".key"]
    file_path_lower = file_path.lower()
    return any(pattern in file_path_lower for pattern in sensitive_patterns)

def log_event(session_id, tool_name, file_path, file_size):
    """记录事件到日志"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "post_tool_events.jsonl"

    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "tool_name": tool_name,
        "file_path": file_path,
        "file_size": file_size
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

if __name__ == "__main__":
    main()
