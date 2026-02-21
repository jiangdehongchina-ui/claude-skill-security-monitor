# Skill Security Monitoring System

Claude Code 技能安全监控系统 — 基于五层 Pipeline 架构的实时安全防护

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Tests](https://img.shields.io/badge/tests-61%20passed-success)

## 概述

本系统为 Claude Code Skills 提供全面的安全监控，通过 PreToolUse Hook 拦截每一次工具调用，经过五层安全检测管道后决定放行或拒绝。

**五层防护架构：**

1. **Input Validation** — 输入验证（规范化预处理 + 注入检测）
2. **Permission Control** — 权限控制（命令白名单 + 路径黑名单）
3. **Pattern Detection** — 模式检测（43 条正则规则）
4. **Content Scanning** — 内容扫描（16 种云凭证 + 数据外传检测）
5. **Audit Logging** — 审计日志（JSONL 格式 + 自动轮转）

## 特性

- 模块化 Pipeline 架构，每层独立可插拔
- fail-closed 安全策略（配置异常时拒绝执行）
- Prompt 类型 Hook 语义分析（AI 辅助判断）
- 规范化预处理防止 URL 编码、零宽字符绕过
- 实时终端监控 UI（彩色显示、过滤、统计）
- 白名单管理、配置验证、完整性校验
- 61 个测试用例，100% 通过率

## 安装

### 1. 克隆到 Claude 插件目录

```bash
# Windows
cd %USERPROFILE%\.claude\plugins
git clone https://github.com/jiangdehongchina-ui/claude-skill-security-monitor.git skill-jiankong

# Linux/macOS
cd ~/.claude/plugins
git clone https://github.com/jiangdehongchina-ui/claude-skill-security-monitor.git skill-jiankong
```

### 2. 安装依赖

```bash
cd skill-jiankong
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python hooks/validate_config.py   # 配置验证
python tests/test_hooks.py        # 运行测试
```

重启 Claude Code 会话，Hook 将自动生效。

## 实时监控 UI

在单独的终端窗口中启动监控界面：

```bash
python monitor_ui.py
```

```
╔══════════════════════════════════════════════════════════════╗
║  Skill Security Monitor                                      ║
║  Events: 799 | Blocked: 231 | Allowed: 568 | Rate: 28.9%    ║
╠══════════════════════════════════════════════════════════════╣
║ TIME     │ TOOL  │ DECISION │ REASON              │ MS      ║
║ 10:30:00 │ Bash  │   DENY   │ Command injection   │ 12.5    ║
║ 10:30:05 │ Write │  ALLOW   │ All checks passed   │  3.2    ║
╠══════════════════════════════════════════════════════════════╣
║ [q]Quit [f]Filter [d]Decision [c]Clear [s]Stats [p]Pause    ║
╚══════════════════════════════════════════════════════════════╝
```

启动参数：

```bash
python monitor_ui.py --filter-tool Bash        # 只看 Bash 事件
python monitor_ui.py --filter-decision deny    # 只看拦截事件
python monitor_ui.py --no-stats                # 隐藏统计面板
```

## 配置

### permissions.yaml — 权限规则

```yaml
permissions:
  allowed_commands:
    git: [status, diff, log, add, commit, push, pull]
    npm: [install, test, run, build]
    python: ["*.py", "-m pytest", "-m pip"]
  blocked_commands: [sudo, su, chmod, dd, shutdown, reboot]
  blocked_paths:
    - "C:\\Windows\\System32\\**"
    - "**/.env"
    - "**/.ssh/**"
    - "**/.aws/credentials"
```

### patterns.yaml — 检测规则（43 条）

覆盖：命令注入（14）、路径穿越（6）、凭证泄露（14）、危险代码（9）、SQL 注入、XSS、数据外传

## 白名单管理

```bash
python hooks/whitelist_manager.py list                              # 列出
python hooks/whitelist_manager.py add Bash "git status" --reason "Safe"  # 添加
python hooks/whitelist_manager.py remove allow-1                    # 删除
```

## 工具集

| 工具 | 用途 |
|------|------|
| `hooks/validate_config.py` | 验证所有配置文件格式 |
| `hooks/check_integrity.py` | SHA256 完整性校验 |
| `hooks/cleanup_logs.py` | 日志清理和轮转 |
| `monitor_ui.py` | 实时终端监控 UI |

## 架构

### Pipeline 执行流程

```
Claude Code Tool Call
    ↓
PreToolUse Hook → stdin JSON {tool_name, tool_input}
    ↓
白名单快速放行检查
    ↓
SecurityPipeline.execute()
    ├── Layer 1: InputValidator    (规范化 + 注入检测)
    ├── Layer 2: PermissionChecker (命令白名单 + 路径黑名单)
    ├── Layer 3: PatternDetector   (43 条正则模式匹配)
    ├── Layer 4: ContentScanner    (凭证泄露 + 数据外传)
    └── Layer 5: AuditLogger       (JSONL 日志记录)
    ↓
exit 0 (允许) / exit 2 (拒绝)
```

### 文件结构

```
skill-jiankong/
├── hooks/
│   ├── hooks.json                 # Hook 配置入口
│   ├── security_check.py          # 主入口（Pipeline 调度）
│   ├── post_write_check.py        # PostToolUse 写入验证
│   ├── whitelist_manager.py       # 白名单 CLI
│   ├── validate_config.py         # 配置验证
│   ├── check_integrity.py         # 完整性校验
│   ├── cleanup_logs.py            # 日志清理
│   ├── core/
│   │   ├── pipeline.py            # SecurityPipeline 管道
│   │   ├── models.py              # HookInput, ValidationResult
│   │   └── config_loader.py       # 配置加载（带缓存）
│   ├── validators/
│   │   ├── base.py                # BaseValidator 抽象基类
│   │   ├── input_validator.py     # Layer 1: 输入验证
│   │   ├── permission_checker.py  # Layer 2: 权限控制
│   │   ├── pattern_detector.py    # Layer 3: 模式检测
│   │   ├── content_scanner.py     # Layer 4: 内容扫描
│   │   └── audit_logger.py        # Layer 5: 审计日志
│   └── config/
│       ├── permissions.yaml       # 权限规则
│       ├── patterns.yaml          # 检测模式（43条）
│       └── whitelist.json         # 白名单数据
├── tests/
│   └── test_hooks.py              # 61 个测试用例
├── monitor_ui.py                  # 实时监控终端 UI
├── requirements.txt               # PyYAML + rich
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## 测试

```bash
python tests/test_hooks.py
```

61 个测试覆盖：原始功能（8）、五层单元测试（36）、边界条件（10）、白名单（3）、配置容错（2）、性能（2）。

## 版本规划

- **v0.1** ✅ 纯 hook 脚本，基于规则检测，8 个测试
- **v0.2** ✅ 模块化 Pipeline，监控 UI，61 个测试，43 条检测规则
- **v0.3** 🔲 Web dashboard，事件关联分析
- **v1.0** 🔲 ML 异常检测，自适应学习

## 许可证

MIT License

## 链接

- [GitHub](https://github.com/jiangdehongchina-ui/claude-skill-security-monitor)
- [Changelog](CHANGELOG.md)
- [安全改进报告](SECURITY_IMPROVEMENTS.md)
- [测试报告](TEST_REPORT.md)
