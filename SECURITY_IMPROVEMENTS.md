# 安全策略改进方案 (Security Improvements Report)

## 概述

基于对 AI Agent 安全威胁的研究和代码审查，本报告提出五层安全防护策略的改进方案。

---

## Layer 1: 输入验证改进

### 已实施的改进
1. **规范化预处理**：添加 URL 解码（防 `%2e%2e%2f` 绕过）和零宽字符清除
2. **新增注入检测模式**：
   - `base64 decode` 执行
   - `curl | sh` 管道执行
   - `wget -O - |` 管道执行
   - Netcat 反向 shell（`nc -e`, `nc -l`）
   - Bash TCP 设备（`/dev/tcp/`）
   - 命名管道创建（`mkfifo`）
   - 内联脚本执行（`python -c`, `perl -e`, `ruby -e`）

### 建议后续改进
- Unicode 规范化（NFC/NFKC）防止同形字符绕过
- 环境变量展开检测（`${IFS}` 替代空格）
- 嵌套编码检测（双重 URL 编码）

## Layer 2: 权限控制改进

### 已实施的改进
1. **扩展命令白名单**：新增 `npx`, `node`, `cp`, `mv`, `touch`, `head`, `tail`, `wc`, `sort`, `grep`, `find`, `which`, `sleep` 等常用命令
2. **移除危险命令**：`rm` 从白名单移除（需通过 Bash 的其他方式处理）
3. **新增 blocked_commands 列表**：明确禁止 `sudo`, `su`, `chmod`, `chown`, `dd`, `shutdown`, `reboot`, `iptables`, `netsh`, `reg`, `regedit`, `format`, `diskpart` 等
4. **扩展路径黑名单**：新增 `.aws/credentials`, `.azure/`, `.gcloud/`, `credentials.json`

### 建议后续改进
- 基于命令参数的细粒度控制（如 `docker run --privileged` 应被拦截）
- 网络访问控制（限制 curl/wget 的目标域名）

## Layer 3: 模式检测改进

### 已实施的改进
1. **新增检测类别**：`data_exfiltration`（数据外传检测）
   - curl 文件上传（`--data @`, `-F @`）
   - SCP/SFTP/rsync 远程传输
2. **增强 SQL 注入检测**：时间盲注（`WAITFOR DELAY`）、MySQL benchmark 注入
3. **增强 XSS 检测**：SVG XSS、img onerror XSS
4. **增强凭证检测**：GitHub PAT、OpenAI key、Anthropic key、Slack token、SendGrid key、Google API key、数据库连接字符串

### 建议后续改进
- 上下文感知检测（区分代码注释中的模式 vs 实际执行的模式）
- 降低 `;\s*\w+` 等宽泛模式的误报率

## Layer 4: 内容扫描改进

### 已实施的改进
1. **内置云服务凭证检测**：16 种云服务 token 模式（独立于 patterns.yaml）
2. **数据外传行为检测**：curl 上传、wget POST、SCP、rsync、FTP/SFTP

### 建议后续改进
- 文件内容中的 prompt injection 检测
- 恶意 SKILL.md 指令注入检测
- 二进制文件写入检测

## Layer 5: 审计响应改进

### 已实施的改进
1. **增强日志字段**：新增 `severity`、`violation_type` 字段
2. **精确计时**：`execution_time_ms` 精确到小数点后两位
3. **日志轮转**：10MB 自动归档

### 建议后续改进
- 日志中敏感信息脱敏（API key 只记录前 4 位）
- 事件关联分析（检测 Read .env → Bash curl 序列）

## AI 特有安全威胁

### 需要关注的威胁
1. **Indirect Prompt Injection**：恶意文件内容中嵌入指令，被 AI 读取后执行
2. **Tool Poisoning**：恶意 skill 通过 SKILL.md 注入危险工具权限
3. **Confused Deputy**：AI 被诱导执行超出用户意图的操作
4. **Supply Chain**：第三方 skill 包含恶意代码

### 防护建议
- 利用 Claude Code 的 prompt 类型 hook 进行语义级分析
- 对 SKILL.md 文件进行安全审计
- 监控异常的工具调用序列
