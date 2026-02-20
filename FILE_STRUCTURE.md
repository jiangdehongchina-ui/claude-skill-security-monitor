# Skill Security Monitoring System - 完整文件结构

## 目录位置
**主目录**: `C:\Users\jiang\claude\skill-jiankong\skill-jiankong\`

## 完整文件树

```
skill-jiankong/
├── hooks/                          # Hook脚本和工具目录
│   ├── hooks.json                  # Claude Code Hook配置文件 ⭐
│   ├── security_check.py           # 主安全检测脚本（五层架构）⭐
│   ├── post_write_check.py         # PostToolUse检查脚本
│   ├── whitelist_manager.py        # 白名单管理CLI工具
│   ├── validate_config.py          # 配置验证工具 🆕
│   ├── check_integrity.py          # 完整性校验工具 🆕
│   ├── cleanup_logs.py             # 日志清理工具 🆕
│   ├── setup_permissions.sh        # 权限设置脚本 🆕
│   ├── config/                     # 配置文件目录
│   │   ├── permissions.yaml        # 权限配置（命令白名单、路径黑名单）
│   │   ├── patterns.yaml           # 检测规则（正则表达式模式）
│   │   ├── whitelist.json          # 用户白名单数据
│   │   └── .checksums.json         # 配置文件SHA256校验和 🆕
│   └── validators/                 # 验证器模块目录（预留）
│
├── logs/                           # 日志文件目录
│   ├── security_events.jsonl       # 安全事件日志（JSON Lines格式）
│   └── post_tool_events.jsonl      # PostToolUse事件日志
│
├── tests/                          # 测试目录
│   └── test_hooks.py               # 集成测试（8个测试用例）
│
├── README.md                       # 项目说明文档
├── IMPLEMENTATION_SUMMARY.md       # 实施总结文档
├── requirements.txt                # Python依赖（PyYAML>=6.0）
│
└── skill-jiankong/                 # 嵌套目录（包含额外文档）
    ├── deploy.sh                   # 一键部署脚本
    ├── PROJECT_REVIEW.md           # 项目审查报告
    └── OPTIMIZATION_REPORT.md      # 优化完成报告 🆕
```

## 文件统计

### 核心文件（8个）
1. hooks.json - Hook配置
2. security_check.py - 主检测脚本（365行）
3. post_write_check.py - PostToolUse检查
4. whitelist_manager.py - 白名单管理
5. permissions.yaml - 权限配置
6. patterns.yaml - 检测规则
7. whitelist.json - 白名单数据
8. test_hooks.py - 测试套件

### 新增工具（4个）🆕
1. validate_config.py - 配置验证
2. check_integrity.py - 完整性校验
3. cleanup_logs.py - 日志清理
4. setup_permissions.sh - 权限设置

### 文档文件（5个）
1. README.md - 使用文档
2. IMPLEMENTATION_SUMMARY.md - 实施总结
3. PROJECT_REVIEW.md - 审查报告
4. OPTIMIZATION_REPORT.md - 优化报告
5. FILE_STRUCTURE.md - 本文件

### 配置/数据文件（4个）
1. requirements.txt - 依赖
2. .checksums.json - 校验和
3. security_events.jsonl - 日志
4. post_tool_events.jsonl - 日志

## 关键文件说明

### ⭐ hooks.json
**作用**: Claude Code的hook配置文件
**位置**: `hooks/hooks.json`
**关键点**:
- 外层必须有`"hooks"`键
- 超时单位是秒（不是毫秒）
- 包含PreToolUse和PostToolUse两种hook

### ⭐ security_check.py
**作用**: 主安全检测脚本
**位置**: `hooks/security_check.py`
**行数**: 365行
**关键点**:
- 从stdin读取JSON输入
- 使用tool_name和tool_input字段
- 实现五层安全检测
- fail-closed策略
- 正则表达式预编译缓存
- 性能监控（execution_time_ms）

### 配置文件
**permissions.yaml**: 11个允许命令 + 18个阻止路径
**patterns.yaml**: 24个检测模式（7类攻击）
**whitelist.json**: 用户批准的操作列表

## 部署位置

### 当前位置（开发）
```
C:\Users\jiang\claude\skill-jiankong\skill-jiankong\
```

### 生产部署位置（推荐）
```
C:\Users\jiang\.claude\plugins\skill-jiankong\
```

## 架构说明

### 🔴 这是一个纯客户端系统，没有服务器端！

**架构类型**: **单机Hook脚本系统**

**工作原理**:
1. Claude Code在本地运行
2. 每次工具调用触发PreToolUse hook
3. Hook脚本在本地执行检测
4. 返回exit code（0=允许，2=拒绝）
5. 日志记录在本地文件

**没有服务器端的原因**:
- MVP v0.1设计为轻量级纯hook方案
- 所有检测在本地完成，无需网络通信
- 配置和日志都在本地文件系统
- 性能最优（无网络延迟）

**未来版本规划**:
- v0.2: 可选的本地daemon（Flask REST API）
- v0.3: 可选的Web dashboard（本地服务）
- v1.0: 可选的集中式监控服务器（团队版）

### 当前版本特点
✅ 纯本地运行
✅ 无需网络
✅ 无需额外服务
✅ 配置即用
✅ 性能最优

## 文件大小统计

```
hooks/security_check.py:      ~15 KB
hooks/config/patterns.yaml:   ~3 KB
hooks/config/permissions.yaml: ~1 KB
logs/security_events.jsonl:   ~16 KB (会增长)
README.md:                    ~5 KB
PROJECT_REVIEW.md:            ~14 KB
OPTIMIZATION_REPORT.md:       ~8 KB
```

**总大小**: 约 100 KB（不含日志）

## 依赖关系

```
security_check.py
    ├── 读取 → hooks/config/permissions.yaml
    ├── 读取 → hooks/config/patterns.yaml
    ├── 读取 → hooks/config/whitelist.json
    └── 写入 → logs/security_events.jsonl

post_write_check.py
    └── 写入 → logs/post_tool_events.jsonl

whitelist_manager.py
    └── 读写 → hooks/config/whitelist.json

validate_config.py
    ├── 读取 → hooks/config/*.yaml
    └── 读取 → hooks/hooks.json

check_integrity.py
    ├── 读取 → hooks/config/*
    └── 读写 → hooks/config/.checksums.json

cleanup_logs.py
    └── 管理 → logs/*.jsonl
```

## 执行权限要求

### Windows
- Python脚本: 无需特殊权限
- 配置文件: 建议设置只读（可选）

### Linux/macOS
```bash
chmod +x hooks/*.py
chmod +x hooks/*.sh
chmod 400 hooks/config/*.yaml  # 只读保护
chmod 400 hooks/config/*.json  # 只读保护
```

## 总结

✅ **所有文件都在**: `C:\Users\jiang\claude\skill-jiankong\skill-jiankong\`
✅ **架构**: 纯客户端，无服务器端
✅ **核心文件**: 8个
✅ **新增工具**: 4个
✅ **文档**: 5个
✅ **总大小**: ~100 KB
✅ **依赖**: 仅PyYAML
✅ **测试**: 8/8通过

