#!/usr/bin/env python3
"""
Configuration Validator - 配置文件验证工具
"""
import sys
import json
import yaml
from pathlib import Path

def validate_yaml(file_path, schema_name):
    """验证YAML文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        print(f"[OK] {schema_name}: Valid YAML syntax")
        return data, True
    except yaml.YAMLError as e:
        print(f"[ERROR] {schema_name}: Invalid YAML - {e}")
        return None, False
    except FileNotFoundError:
        print(f"[ERROR] {schema_name}: File not found - {file_path}")
        return None, False

def validate_json(file_path, schema_name):
    """验证JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[OK] {schema_name}: Valid JSON syntax")
        return data, True
    except json.JSONDecodeError as e:
        print(f"[ERROR] {schema_name}: Invalid JSON - {e}")
        return None, False
    except FileNotFoundError:
        print(f"[ERROR] {schema_name}: File not found - {file_path}")
        return None, False

def validate_permissions(data):
    """验证permissions.yaml结构"""
    if not data:
        return False

    errors = []

    # 检查必需字段
    if "permissions" not in data:
        errors.append("Missing 'permissions' key")
    else:
        perms = data["permissions"]
        if "allowed_commands" not in perms:
            errors.append("Missing 'permissions.allowed_commands'")
        if "blocked_paths" not in perms:
            errors.append("Missing 'permissions.blocked_paths'")

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False

    print(f"  [OK] Structure valid")
    print(f"  [INFO] Allowed commands: {len(data['permissions'].get('allowed_commands', {}))}")
    print(f"  [INFO] Blocked paths: {len(data['permissions'].get('blocked_paths', []))}")
    return True

def validate_patterns(data):
    """验证patterns.yaml结构"""
    if not data:
        return False

    errors = []
    pattern_types = ["command_injection", "path_traversal", "credentials", "dangerous_code"]

    for ptype in pattern_types:
        if ptype not in data:
            errors.append(f"Missing pattern type: {ptype}")
        else:
            patterns = data[ptype]
            if not isinstance(patterns, list):
                errors.append(f"{ptype} should be a list")
            else:
                for i, p in enumerate(patterns):
                    if "pattern" not in p:
                        errors.append(f"{ptype}[{i}]: Missing 'pattern' field")
                    if "severity" not in p:
                        errors.append(f"{ptype}[{i}]: Missing 'severity' field")
                    if "description" not in p:
                        errors.append(f"{ptype}[{i}]: Missing 'description' field")

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False

    print(f"  [OK] Structure valid")
    for ptype in pattern_types:
        if ptype in data:
            print(f"  [INFO] {ptype}: {len(data[ptype])} patterns")
    return True

def validate_hooks(data):
    """验证hooks.json结构"""
    if not data:
        return False

    errors = []

    # 检查外层hooks键
    if "hooks" not in data:
        errors.append("Missing outer 'hooks' key (CRITICAL)")
        print(f"  [ERROR] {errors[0]}")
        return False

    hooks = data["hooks"]

    # 检查PreToolUse
    if "PreToolUse" not in hooks:
        errors.append("Missing 'hooks.PreToolUse'")
    else:
        for i, entry in enumerate(hooks["PreToolUse"]):
            if "hooks" not in entry:
                errors.append(f"PreToolUse[{i}]: Missing 'hooks' field")
            else:
                for j, hook in enumerate(entry["hooks"]):
                    if "type" not in hook:
                        errors.append(f"PreToolUse[{i}].hooks[{j}]: Missing 'type'")
                    if "timeout" in hook and not isinstance(hook["timeout"], (int, float)):
                        errors.append(f"PreToolUse[{i}].hooks[{j}]: 'timeout' should be a number (seconds)")

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False

    print(f"  [OK] Structure valid")
    print(f"  [OK] Has outer 'hooks' key")
    return True

def validate_whitelist(data):
    """验证whitelist.json结构"""
    if not data:
        return False

    errors = []

    if "version" not in data:
        errors.append("Missing 'version' field")
    if "entries" not in data:
        errors.append("Missing 'entries' field")
    elif not isinstance(data["entries"], list):
        errors.append("'entries' should be a list")

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False

    print(f"  [OK] Structure valid")
    print(f"  [INFO] Whitelist entries: {len(data['entries'])}")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("Configuration Validator")
    print("=" * 60)
    print()

    base_dir = Path(__file__).parent
    config_dir = base_dir / "config"

    all_valid = True

    # 验证permissions.yaml
    print("[1/4] Validating permissions.yaml...")
    data, valid = validate_yaml(config_dir / "permissions.yaml", "permissions.yaml")
    if valid:
        valid = validate_permissions(data)
    all_valid = all_valid and valid
    print()

    # 验证patterns.yaml
    print("[2/4] Validating patterns.yaml...")
    data, valid = validate_yaml(config_dir / "patterns.yaml", "patterns.yaml")
    if valid:
        valid = validate_patterns(data)
    all_valid = all_valid and valid
    print()

    # 验证hooks.json
    print("[3/4] Validating hooks.json...")
    data, valid = validate_json(base_dir / "hooks.json", "hooks.json")
    if valid:
        valid = validate_hooks(data)
    all_valid = all_valid and valid
    print()

    # 验证whitelist.json
    print("[4/4] Validating whitelist.json...")
    data, valid = validate_json(config_dir / "whitelist.json", "whitelist.json")
    if valid:
        valid = validate_whitelist(data)
    all_valid = all_valid and valid
    print()

    # 总结
    print("=" * 60)
    if all_valid:
        print("Result: ALL CONFIGURATIONS VALID")
        print("=" * 60)
        sys.exit(0)
    else:
        print("Result: VALIDATION FAILED")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
