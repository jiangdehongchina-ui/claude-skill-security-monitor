"""
Tests for security_check.py hook
"""
import json
import subprocess
import sys
from pathlib import Path

# 测试数据
TEST_CASES = [
    {
        "name": "Command injection - should block",
        "input": {
            "session_id": "test-001",
            "tool_name": "Bash",
            "tool_input": {"command": "ls; rm -rf /"}
        },
        "expected_exit": 2,
        "expected_stderr_contains": "Command injection"
    },
    {
        "name": "Path traversal - should block",
        "input": {
            "session_id": "test-002",
            "tool_name": "Write",
            "tool_input": {"file_path": "../../../etc/passwd", "content": "test"}
        },
        "expected_exit": 2,
        "expected_stderr_contains": "Path traversal"
    },
    {
        "name": "System path - should block",
        "input": {
            "session_id": "test-003",
            "tool_name": "Write",
            "tool_input": {"file_path": "C:\\Windows\\System32\\test.txt", "content": "test"}
        },
        "expected_exit": 2,
        "expected_stderr_contains": "Blocked path"
    },
    {
        "name": "Unauthorized command - should block",
        "input": {
            "session_id": "test-004",
            "tool_name": "Bash",
            "tool_input": {"command": "sudo rm -rf /"}
        },
        "expected_exit": 2,
        "expected_stderr_contains": "not in whitelist"
    },
    {
        "name": "Dangerous command - should block",
        "input": {
            "session_id": "test-005",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /home/user"}
        },
        "expected_exit": 2,
        "expected_stderr_contains": "not in whitelist"  # 被权限检查拦截
    },
    {
        "name": "Credential in content - should block",
        "input": {
            "session_id": "test-006",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "test.py",
                "content": "API_KEY=sk12345678901234567890"
            }
        },
        "expected_exit": 2,
        "expected_stderr_contains": "Credential"
    },
    {
        "name": "Safe git command - should allow",
        "input": {
            "session_id": "test-007",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"}
        },
        "expected_exit": 0,
        "expected_stderr_contains": None
    },
    {
        "name": "Safe write - should allow",
        "input": {
            "session_id": "test-008",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "test.txt",
                "content": "Hello World"
            }
        },
        "expected_exit": 0,
        "expected_stderr_contains": None
    }
]

def run_test(test_case):
    """运行单个测试用例"""
    print(f"\nTest: {test_case['name']}")

    # 准备输入
    input_data = json.dumps(test_case["input"])

    # 运行hook脚本
    result = subprocess.run(
        [sys.executable, "hooks/security_check.py"],
        input=input_data,
        capture_output=True,
        text=True
    )

    # 检查exit code
    if result.returncode != test_case["expected_exit"]:
        print(f"  [FAIL] Expected exit code {test_case['expected_exit']}, got {result.returncode}")
        print(f"    stderr: {result.stderr}")
        return False

    # 检查stderr内容
    if test_case["expected_stderr_contains"]:
        if test_case["expected_stderr_contains"] not in result.stderr:
            print(f"  [FAIL] Expected stderr to contain '{test_case['expected_stderr_contains']}'")
            print(f"    stderr: {result.stderr}")
            return False

    print(f"  [PASS]")
    return True

def main():
    """运行所有测试"""
    print("=" * 60)
    print("Running Security Check Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_case in TEST_CASES:
        if run_test(test_case):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
