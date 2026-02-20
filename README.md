# Skill Security Monitoring System

Claude Code技能安全监控系统 - 基于五层安全架构的实时监控方案

## 概述

本系统为Claude Code skills提供全面的安全监控，实现五层防护策略：

1. **Input Validation** - 输入验证层
2. **Permission Control** - 权限控制层
3. **Runtime Monitoring** - 运行时监控层
4. **Content Security** - 内容安全层
5. **Audit and Response** - 审计响应层

## 特性

- ✅ 修正所有Claude Code hook集成错误（stdin读取、正确字段名、hooks.json格式）
- ✅ fail-closed安全策略（配置加载失败时拒绝执行）
- ✅ Prompt类型hook语义分析
- ✅ 规范化预处理防止绕过攻击
- ✅ 命令注入、路径穿越、凭证泄露检测
- ✅ 白名单管理系统
- ✅ JSON Lines审计日志

## 安装

### 1. 克隆到Claude插件目录

```bash
# Windows
cd C:\Users\jiang\.claude\plugins
git clone <repository-url> skill-jiankong

# Linux/macOS
cd ~/.claude/plugins
git clone <repository-url> skill-jiankong
```

### 2. 安装依赖

```bash
cd skill-jiankong
pip install -r requirements.txt
```

### 3. 初始化配置

```bash
python hooks/whitelist_manager.py init
```

### 4. 设置可执行权限（Linux/macOS）

```bash
chmod +x hooks/security_check.py
chmod +x hooks/post_write_check.py
chmod +x hooks/whitelist_manager.py
```

## 配置

### permissions.yaml

定义允许的命令和路径：

```yaml
permissions:
  allowed_commands:
    git: [status, diff, log, add, commit, push]
    npm: [install, test, run]
    python: ["*.py", "-m pytest"]

  blocked_paths:
    - "C:\\Windows\\System32\\**"
    - "**/.env"
    - "**/.ssh/**"
```

### patterns.yaml

定义安全检测规则：

```yaml
command_injection:
  - {pattern: '\$\([^)]+\)', severity: high}

credentials:
  - {pattern: '(?i)api[_-]?key\s*[:=]\s*[\w\-]{20,}', severity: critical}
```

## 使用

### 白名单管理

```bash
# 列出所有白名单条目
python hooks/whitelist_manager.py list

# 添加白名单条目
python hooks/whitelist_manager.py add Bash "*git status*" --reason "Safe command"

# 删除白名单条目
python hooks/whitelist_manager.py remove allow-1
```

### 查看日志

```bash
# 查看安全事件日志
cat logs/security_events.jsonl

# 查看最近10条
tail -n 10 logs/security_events.jsonl

# 查看被拒绝的操作
grep '"decision": "deny"' logs/security_events.jsonl
```

## 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_hooks.py -v
```

## 工作原理

### Hook执行流程

```
Claude Code Tool Call
    ↓
PreToolUse Hook触发
    ↓
从stdin读取JSON（tool_name, tool_input）
    ↓
检查白名单
    ↓
Layer 1: 输入验证（命令注入、路径穿越）
    ↓
Layer 2: 权限检查（命令白名单）
    ↓
Layer 3: 模式检测（危险命令序列）
    ↓
Layer 4: 内容扫描（凭证、危险代码）
    ↓
Layer 5: 审计日志
    ↓
返回决策（exit 0=允许, exit 2=拒绝）
```

### 安全策略

- **fail-closed**: 配置加载失败时拒绝执行
- **规范化预处理**: URL解码、大小写规范化防止绕过
- **多层检测**: 正则+语义分析双重验证
- **审计追踪**: 所有操作记录到JSON Lines日志

## 文件结构

```
skill-jiankong/
├── hooks/
│   ├── hooks.json                 # Hook配置
│   ├── security_check.py          # 主检测脚本
│   ├── post_write_check.py        # PostToolUse检查
│   ├── whitelist_manager.py       # 白名单管理CLI
│   └── config/
│       ├── permissions.yaml       # 权限配置
│       ├── patterns.yaml          # 检测规则
│       └── whitelist.json         # 白名单数据
├── logs/
│   ├── security_events.jsonl      # 安全事件日志
│   └── post_tool_events.jsonl     # PostToolUse日志
├── tests/
│   └── test_hooks.py              # 测试用例
├── requirements.txt
└── README.md
```

## 常见问题

### Q: Hook没有被触发？

A: 检查以下几点：
1. 确认hooks.json在正确位置
2. 确认Python脚本有执行权限
3. 查看Claude Code日志是否有错误

### Q: 所有操作都被拒绝？

A: 可能是配置文件加载失败（fail-closed策略）：
1. 检查permissions.yaml和patterns.yaml格式
2. 确认PyYAML已安装
3. 查看stderr输出的错误信息

### Q: 如何临时禁用监控？

A: 重命名hooks.json：
```bash
mv hooks/hooks.json hooks/hooks.json.disabled
```

## 版本规划

- **v0.1 (当前)**: 纯hook脚本，基于规则检测
- **v0.2**: 引入daemon，SQLite持久化，Windows通知
- **v0.3**: Web dashboard，实时监控
- **v1.0**: ML异常检测，自适应学习

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: [项目地址]
- Issues: [问题追踪]
