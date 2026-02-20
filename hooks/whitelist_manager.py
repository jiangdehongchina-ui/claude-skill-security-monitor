#!/usr/bin/env python3
"""
Whitelist Manager - 白名单管理CLI工具
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

WHITELIST_FILE = Path(__file__).parent / "config" / "whitelist.json"

def load_whitelist():
    """加载白名单"""
    if WHITELIST_FILE.exists():
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "1.0", "entries": []}

def save_whitelist(whitelist):
    """保存白名单"""
    WHITELIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, indent=2, ensure_ascii=False)

def add_entry(tool_name, pattern, reason):
    """添加白名单条目"""
    whitelist = load_whitelist()

    entry = {
        "id": f"allow-{len(whitelist['entries']) + 1}",
        "tool": tool_name,
        "pattern": pattern,
        "reason": reason,
        "added_at": datetime.utcnow().isoformat() + "Z"
    }

    whitelist["entries"].append(entry)
    save_whitelist(whitelist)

    print(f"✓ Added whitelist entry: {entry['id']}")
    print(f"  Tool: {tool_name}")
    print(f"  Pattern: {pattern}")

def remove_entry(entry_id):
    """删除白名单条目"""
    whitelist = load_whitelist()

    original_count = len(whitelist["entries"])
    whitelist["entries"] = [e for e in whitelist["entries"] if e["id"] != entry_id]

    if len(whitelist["entries"]) < original_count:
        save_whitelist(whitelist)
        print(f"✓ Removed whitelist entry: {entry_id}")
    else:
        print(f"✗ Entry not found: {entry_id}")
        sys.exit(1)

def list_entries():
    """列出所有白名单条目"""
    whitelist = load_whitelist()

    if not whitelist["entries"]:
        print("No whitelist entries found.")
        return

    print(f"Whitelist entries ({len(whitelist['entries'])} total):\n")

    for entry in whitelist["entries"]:
        print(f"ID: {entry['id']}")
        print(f"  Tool: {entry['tool']}")
        print(f"  Pattern: {entry.get('pattern', 'N/A')}")
        print(f"  Reason: {entry.get('reason', 'N/A')}")
        print(f"  Added: {entry.get('added_at', 'N/A')}")
        print()

def init_whitelist():
    """初始化白名单配置"""
    whitelist = {"version": "1.0", "entries": []}
    save_whitelist(whitelist)
    print(f"✓ Initialized whitelist at: {WHITELIST_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Whitelist Manager for Skill Security Monitor")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # add命令
    add_parser = subparsers.add_parser("add", help="Add whitelist entry")
    add_parser.add_argument("tool", help="Tool name (e.g., Bash, Write)")
    add_parser.add_argument("pattern", help="Pattern to match")
    add_parser.add_argument("--reason", default="User approved", help="Reason for whitelisting")

    # remove命令
    remove_parser = subparsers.add_parser("remove", help="Remove whitelist entry")
    remove_parser.add_argument("entry_id", help="Entry ID to remove")

    # list命令
    subparsers.add_parser("list", help="List all whitelist entries")

    # init命令
    subparsers.add_parser("init", help="Initialize whitelist configuration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "add":
        add_entry(args.tool, args.pattern, args.reason)
    elif args.command == "remove":
        remove_entry(args.entry_id)
    elif args.command == "list":
        list_entries()
    elif args.command == "init":
        init_whitelist()

if __name__ == "__main__":
    main()
