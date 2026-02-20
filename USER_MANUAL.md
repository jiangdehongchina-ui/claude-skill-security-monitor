# Skill Security Monitoring System - 完整用户手册

**版本**: v0.1 MVP
**更新日期**: 2026-02-20

---

## 📚 手册说明

本手册是系统的完整使用指南，包含所有必要信息。

---

## 目录

1. [分享指南](#分享指南)
2. [文件清单](#文件清单)
3. [部署要求](#部署要求)
4. [部署命令](#部署命令)
5. [日志查询](#日志查询)
6. [常用命令](#常用命令)
7. [故障排查](#故障排查)

---

## 分享指南

### ✅ 可以分享

这个系统完全可以分享给其他人使用。

### 分享方式

**压缩包分享**:
```bash
tar -czf skill-jiankong-v0.1.tar.gz skill-jiankong/
```

**分享前清理**:
```bash
rm -f logs/*.jsonl
echo '{"version": "1.0", "entries": []}' > hooks/config/whitelist.json
```

---

## 文件清单

### 核心文件（8个）

| 文件 | 大小 | 说明 |
|------|------|------|
| hooks/hooks.json | 906 B | Hook配置 |
| hooks/security_check.py | 13 KB | 主检测脚本 |
| hooks/post_write_check.py | 2 KB | PostToolUse检查 |
| hooks/whitelist_manager.py | 3.7 KB | 白名单管理 |
| hooks/config/permissions.yaml | 1.2 KB | 权限配置 |
| hooks/config/patterns.yaml | 3.2 KB | 检测规则 |
| hooks/config/whitelist.json | 40 B | 白名单数据 |
| tests/test_hooks.py | 4.2 KB | 测试套件 |

### 新增工具（4个）

| 文件 | 大小 | 说明 |
|------|------|------|
| hooks/validate_config.py | 6.5 KB | 配置验证 |
| hooks/check_integrity.py | 3.8 KB | 完整性校验 |
| hooks/cleanup_logs.py | 3.7 KB | 日志清理 |
| hooks/setup_permissions.sh | 1.9 KB | 权限设置 |

**总大小**: 约 75 KB（不含日志）

---

## 部署要求

### 操作系统
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 20.04+, Debian 10+, CentOS 8+)

### Python环境
- ✅ Python 3.9+ (最低)
- ✅ Python 3.12+ (推荐)
- ✅ PyYAML >= 6.0

### 必需组件
- ✅ Claude Code CLI 已安装

### 资源需求
- 磁盘: ~100 KB (程序) + 日志
- 内存: < 10 MB
- CPU: < 1%
- 网络: ❌ 不需要

---

## 部署命令

### 快速部署（推荐）

```bash
# 1. 复制到插件目录
cp -r skill-jiankong ~/.claude/plugins/

# 2. 安装依赖
cd ~/.claude/plugins/skill-jiankong
pip install -r requirements.txt

# 3. 验证安装
python hooks/validate_config.py
python tests/test_hooks.py

# 4. 生成校验和
python hooks/check_integrity.py --generate

# 5. 完成！重启Claude Code
```

### Windows部署

```powershell
# PowerShell命令
Copy-Item -Recurse skill-jiankong "$env:USERPROFILE\.claude\plugins\"
cd "$env:USERPROFILE\.claude\plugins\skill-jiankong"
pip install -r requirements.txt
python tests/test_hooks.py
```

### Linux/macOS部署

```bash
# 复制文件
cp -r skill-jiankong ~/.claude/plugins/

# 设置权限
cd ~/.claude/plugins/skill-jiankong
chmod +x hooks/*.py hooks/*.sh

# 安装依赖
pip3 install -r requirements.txt

# 验证
python3 tests/test_hooks.py
```

---

## 日志查询

### 基本查询

```bash
# 查看所有日志
cat logs/security_events.jsonl

# 查看最近10条
tail -n 10 logs/security_events.jsonl

# 实时监控
tail -f logs/security_events.jsonl
```

### 过滤查询

```bash
# 查看被拒绝的操作
grep '"decision": "deny"' logs/security_events.jsonl

# 查看允许的操作
grep '"decision": "allow"' logs/security_events.jsonl

# 查看Bash命令日志
grep '"tool_name": "Bash"' logs/security_events.jsonl

# 查看高危操作
grep '"severity": "critical"' logs/security_events.jsonl
```

### 日志统计

```bash
# 查看日志统计
python hooks/cleanup_logs.py --stats

# 统计拒绝次数
grep -c '"decision": "deny"' logs/security_events.jsonl

# 统计允许次数
grep -c '"decision": "allow"' logs/security_events.jsonl
```

### 日志清理

```bash
# 查看将要删除的日志（dry-run）
python hooks/cleanup_logs.py --days 90 --dry-run

# 实际清理90天前的日志
python hooks/cleanup_logs.py --days 90
```

---

## 常用命令

### 配置管理

```bash
# 验证配置
python hooks/validate_config.py

# 检查完整性
python hooks/check_integrity.py

# 生成校验和
python hooks/check_integrity.py --generate
```

### 白名单管理

```bash
# 列出白名单
python hooks/whitelist_manager.py list

# 添加白名单
python hooks/whitelist_manager.py add Bash "*git status*"

# 删除白名单
python hooks/whitelist_manager.py remove allow-1
```

### 测试命令

```bash
# 运行所有测试
python tests/test_hooks.py

# 预期结果: 8 passed, 0 failed
```

---

## 故障排查

### 问题1: Python版本过低

**症状**: `SyntaxError: invalid syntax`

**解决**:
```bash
python --version  # 检查版本
# 升级到Python 3.9+
```

### 问题2: PyYAML未安装

**症状**: `ModuleNotFoundError: No module named 'yaml'`

**解决**:
```bash
pip install PyYAML>=6.0
```

### 问题3: Hook未触发

**症状**: 命令执行但无安全检查

**检查**:
```bash
# 1. 确认文件位置
ls ~/.claude/plugins/skill-jiankong/hooks/hooks.json

# 2. 验证配置
python hooks/validate_config.py

# 3. 重启Claude Code
```

### 问题4: 测试失败

**症状**: 测试不通过

**解决**:
```bash
# 1. 检查配置
python hooks/validate_config.py

# 2. 重新生成校验和
python hooks/check_integrity.py --generate

# 3. 重新运行测试
python tests/test_hooks.py
```

---

## 快速参考卡

### 一键命令

```bash
# 部署
cp -r skill-jiankong ~/.claude/plugins/ && cd ~/.claude/plugins/skill-jiankong && pip install -r requirements.txt && python tests/test_hooks.py

# 验证
python hooks/validate_config.py && python hooks/check_integrity.py

# 查看日志
tail -n 20 logs/security_events.jsonl

# 清理日志
python hooks/cleanup_logs.py --days 90
```

### 重要路径

```
配置目录: ~/.claude/plugins/skill-jiankong/
Hook配置: hooks/hooks.json
主脚本: hooks/security_check.py
日志文件: logs/security_events.jsonl
白名单: hooks/config/whitelist.json
```

---

## 总结

✅ **部署**: 复制文件 + pip install
✅ **运行**: 自动运行，无需手动启动
✅ **日志**: tail/grep 查询
✅ **管理**: whitelist_manager.py
✅ **测试**: python tests/test_hooks.py

**系统状态**: 🟢 Production Ready

---

**更多信息请参考**:
- README.md - 详细使用文档
- DEPLOYMENT_ENVIRONMENT.md - 部署环境说明
- SHARING_GUIDE.md - 分享指南
- OPTIMIZATION_REPORT.md - 优化报告
