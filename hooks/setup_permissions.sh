#!/bin/bash
# Configuration File Permission Setup
# 设置配置文件权限保护

set -e

echo "=========================================="
echo "Configuration File Permission Setup"
echo "=========================================="
echo ""

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$BASE_DIR/config"

# 检测操作系统
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "[INFO] Windows detected - using icacls for permissions"
    IS_WINDOWS=true
else
    echo "[INFO] Unix-like system detected - using chmod"
    IS_WINDOWS=false
fi

echo ""
echo "Setting permissions for configuration files..."
echo ""

# 配置文件列表
CONFIG_FILES=(
    "$CONFIG_DIR/permissions.yaml"
    "$CONFIG_DIR/patterns.yaml"
    "$CONFIG_DIR/whitelist.json"
    "$BASE_DIR/hooks.json"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")

        if [ "$IS_WINDOWS" = true ]; then
            # Windows: 设置为只读
            icacls "$file" /grant:r "$USERNAME:R" /inheritance:r > /dev/null 2>&1
            echo "  [OK] $filename: Set to read-only (Windows)"
        else
            # Unix: 设置为400 (只读)
            chmod 400 "$file"
            echo "  [OK] $filename: Set to 400 (read-only)"
        fi
    else
        echo "  [SKIP] $filename: File not found"
    fi
done

echo ""
echo "=========================================="
echo "Permission setup complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: To modify configuration files, you need to:"
if [ "$IS_WINDOWS" = true ]; then
    echo "  1. Remove read-only attribute"
    echo "  2. Edit the file"
    echo "  3. Run this script again to re-protect"
else
    echo "  1. chmod 600 <file>  # Make writable"
    echo "  2. Edit the file"
    echo "  3. Run this script again to re-protect"
fi
echo ""
