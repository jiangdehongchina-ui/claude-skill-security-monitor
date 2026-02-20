#!/usr/bin/env python3
"""
Configuration Integrity Checker - 配置文件完整性校验工具
使用SHA256哈希值验证配置文件未被篡改
"""
import sys
import json
import hashlib
from pathlib import Path

CHECKSUM_FILE = Path(__file__).parent / "config" / ".checksums.json"

def calculate_sha256(file_path):
    """计算文件的SHA256哈希值"""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except FileNotFoundError:
        return None

def save_checksums(checksums):
    """保存校验和到文件"""
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_FILE, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def load_checksums():
    """加载已保存的校验和"""
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def generate_checksums():
    """生成所有配置文件的校验和"""
    base_dir = Path(__file__).parent
    config_files = {
        "permissions.yaml": base_dir / "config" / "permissions.yaml",
        "patterns.yaml": base_dir / "config" / "patterns.yaml",
        "whitelist.json": base_dir / "config" / "whitelist.json",
        "hooks.json": base_dir / "hooks.json"
    }

    checksums = {}
    print("Generating checksums...")
    for name, path in config_files.items():
        checksum = calculate_sha256(path)
        if checksum:
            checksums[name] = checksum
            print(f"  {name}: {checksum[:16]}...")
        else:
            print(f"  {name}: [NOT FOUND]")

    save_checksums(checksums)
    print(f"\nChecksums saved to: {CHECKSUM_FILE}")
    return checksums

def verify_checksums():
    """验证配置文件完整性"""
    base_dir = Path(__file__).parent
    config_files = {
        "permissions.yaml": base_dir / "config" / "permissions.yaml",
        "patterns.yaml": base_dir / "config" / "patterns.yaml",
        "whitelist.json": base_dir / "config" / "whitelist.json",
        "hooks.json": base_dir / "hooks.json"
    }

    saved_checksums = load_checksums()
    if not saved_checksums:
        print("[WARNING] No saved checksums found. Run with --generate first.")
        return False

    print("Verifying configuration integrity...")
    all_valid = True

    for name, path in config_files.items():
        current_checksum = calculate_sha256(path)
        saved_checksum = saved_checksums.get(name)

        if not current_checksum:
            print(f"  [ERROR] {name}: File not found")
            all_valid = False
        elif not saved_checksum:
            print(f"  [WARNING] {name}: No saved checksum")
            all_valid = False
        elif current_checksum == saved_checksum:
            print(f"  [OK] {name}: Integrity verified")
        else:
            print(f"  [ALERT] {name}: CHECKSUM MISMATCH!")
            print(f"    Expected: {saved_checksum[:16]}...")
            print(f"    Got:      {current_checksum[:16]}...")
            all_valid = False

    return all_valid

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        print("=" * 60)
        print("Configuration Integrity - Generate Checksums")
        print("=" * 60)
        print()
        generate_checksums()
    else:
        print("=" * 60)
        print("Configuration Integrity - Verify")
        print("=" * 60)
        print()
        if verify_checksums():
            print("\n[SUCCESS] All configuration files are intact")
            sys.exit(0)
        else:
            print("\n[FAILURE] Configuration integrity check failed")
            sys.exit(1)

if __name__ == "__main__":
    main()
