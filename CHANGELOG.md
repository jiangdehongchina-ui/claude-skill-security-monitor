# Changelog

## [0.2.0] - 2026-02-21

### 新增
- 模块化 Pipeline 架构（`hooks/core/` + `hooks/validators/`）
- SecurityPipeline 管道模式，五层检测器独立可插拔
- 实时终端监控 UI（`monitor_ui.py`，基于 rich 库）
- Layer 4 内容扫描器：16 种云服务凭证检测（GitHub PAT、OpenAI key、Anthropic key、AWS key、Slack token 等）
- 数据外传行为检测（curl upload、scp、rsync、ftp）
- 高级注入检测（curl|sh、netcat、base64 decode、/dev/tcp、mkfifo）
- `blocked_commands` 明确禁止列表（sudo、dd、shutdown、reboot 等）
- SQL 注入时间盲注检测（WAITFOR DELAY、BENCHMARK）
- SVG/img XSS 检测
- 61 个综合测试用例（100% 通过率）
- 安全审查报告（SECURITY_IMPROVEMENTS.md、DEVILS_ADVOCATE_REPORT.md）
- 测试报告（TEST_REPORT.md）

### 改进
- `security_check.py` 从 365 行单文件拆分为 7 个独立模块
- `patterns.yaml` 从 24 条扩展到 43 条检测模式
- `permissions.yaml` 新增 26 条命令规则和 22 条路径规则
- 配置加载添加模块级缓存，避免重复 I/O
- 正则表达式预编译缓存
- 输入规范化预处理（URL 解码、零宽字符清除）
- 路径黑名单大小写不敏感匹配（Windows 兼容）

### 修复
- `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`（Python 3.12+ 兼容）

## [0.1.0] - 2026-02-20

### 初始版本
- 五层安全防护架构（输入验证、权限控制、模式检测、内容扫描、审计日志）
- PreToolUse / PostToolUse Hook 集成（stdin JSON 协议）
- 命令注入、路径穿越、凭证泄露检测
- 白名单管理 CLI
- 配置验证和 SHA256 完整性校验
- fail-closed 安全策略
- Prompt 类型 Hook 语义分析
- 8 个集成测试
