#!/bin/bash
# Skill Security Monitoring System - 快速部署脚本

set -e

echo "=========================================="
echo "Skill Security Monitor - 部署脚本"
echo "=========================================="
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLUGIN_DIR="$HOME/.claude/plugins/skill-jiankong"
    PYTHON_CMD="python"
else
    PLUGIN_DIR="$HOME/.claude/plugins/skill-jiankong"
    PYTHON_CMD="python3"
fi

echo "目标目录: $PLUGIN_DIR"
echo ""

# 步骤1: 创建目录
echo "[1/6] 创建插件目录..."
mkdir -p "$PLUGIN_DIR"

# 步骤2: 复制文件
echo "[2/6] 复制项目文件..."
cp -r hooks "$PLUGIN_DIR/"
cp -r tests "$PLUGIN_DIR/"
cp requirements.txt "$PLUGIN_DIR/"
cp README.md "$PLUGIN_DIR/"
cp PROJECT_REVIEW.md "$PLUGIN_DIR/"
cp IMPLEMENTATION_SUMMARY.md "$PLUGIN_DIR/"

# 步骤3: 创建日志目录
echo "[3/6] 创建日志目录..."
mkdir -p "$PLUGIN_DIR/logs"

# 步骤4: 安装依赖
echo "[4/6] 安装Python依赖..."
$PYTHON_CMD -m pip install -r "$PLUGIN_DIR/requirements.txt" --user

# 步骤5: 初始化配置
echo "[5/6] 初始化配置..."
cd "$PLUGIN_DIR"
$PYTHON_CMD hooks/whitelist_manager.py init

# 步骤6: 运行测试
echo "[6/6] 运行测试验证..."
$PYTHON_CMD tests/test_hooks.py

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "配置文件位置:"
echo "  - Hook配置: $PLUGIN_DIR/hooks/hooks.json"
echo "  - 权限配置: $PLUGIN_DIR/hooks/config/permissions.yaml"
echo "  - 检测规则: $PLUGIN_DIR/hooks/config/patterns.yaml"
echo "  - 白名单: $PLUGIN_DIR/hooks/config/whitelist.json"
echo ""
echo "日志文件位置:"
echo "  - 安全事件: $PLUGIN_DIR/logs/security_events.jsonl"
echo "  - PostToolUse: $PLUGIN_DIR/logs/post_tool_events.jsonl"
echo ""
echo "常用命令:"
echo "  - 查看日志: tail -f $PLUGIN_DIR/logs/security_events.jsonl"
echo "  - 管理白名单: $PYTHON_CMD $PLUGIN_DIR/hooks/whitelist_manager.py list"
echo "  - 运行测试: $PYTHON_CMD $PLUGIN_DIR/tests/test_hooks.py"
echo ""
echo "下次启动Claude Code时，监控系统将自动生效。"
echo ""
