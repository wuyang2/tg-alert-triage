---
name: tg-alert-triage
description: Diagnose, triage, and respond to Telegram-received backend error alerts (PHP/Phalcon style) that include env/app, request method+URI, params, host, file:line, fingerprint, seen times, and stack trace. Use when the user pastes a TG alarm/exception message (often after @mention in a group) and wants (1) a concise diagnosis hypothesis, (2) prioritized investigation steps (runtime logs/db/deploy/inputs), (3) immediate mitigations, and (4) code-level optimization or hardening suggestions.
---

# Workflow (TG backend alert triage)

## 0) Goal
Produce **actionable output** from an alert paste:
- What happened / scope / severity
- Most likely causes (ranked)
- Next steps (ranked, concrete commands/questions)
- Quick mitigations
- Code hardening & optimization suggestions

Also support a workflow where the user only enables code-context inclusion **temporarily when asking for analysis** (e.g. in a TG thread with @mention). Default posture: do not include code in alerts unless explicitly requested.

## 1) Parse & normalize
From the pasted alert, extract these fields when present:
- env, app, host
- method, uri, module/controller/action
- exception: class/message/code/file/line
- fingerprint, count, first_seen, last_seen
- params payload (redact secrets)
- trace (top frames)
- code context snippet (e.g. "Code(±15)" / surrounding ~30 lines)

If **missing** any of these critical fields, ask *only* for the minimal additions:
- Is this user-facing endpoint? (impact)
- Was there a deploy between first_seen and last_seen?
- Any correlated logs for request_id/trace_id?

## 2) Severity & scope
Use business-impact-first classification (since no formal rules yet):
- **事故（High）**：影响用户正常业务流程 / 功能不可用 / 核心接口持续报错。
- **一般（Medium）**：不影响用户主流程，但会影响某功能、数据准确性、或错误持续增长。
- **提示（Low）**：dev/test 环境、或明显是测试接口/测试异常、或低频且无用户影响。

**常见误判提醒（必须先澄清）**
- PHP `Type=8`（`E_NOTICE/E_WARNING`，例如 `Undefined index`）很多项目会被错误处理器“升级”成 Fatal 告警，但它本质往往是**数据缺字段/兜底缺失**，不一定是进程崩溃。
- 先判断：
  - 这条告警是否真的导致接口 500/流程中断？
  - 还是仅告警升级 + 响应被 warning 文本污染（JSON 解析失败）？

Always state the assumed impact and what evidence is missing.

## 3) Diagnosis hypotheses (ranked)
Rank by:
- proximity of stack top to app code (Controller/Service/Model)
- whether message indicates intentional test vs real exception
- whether params suggest validation / missing required fields
- whether host/local ip indicates local test runner

Include at least:
- "This looks like an intentional test alert" vs "unexpected exception"
- "Input validation / type mismatch" hypothesis
- "dependency (DB/Redis/HTTP)" hypothesis
- "deploy/regression" hypothesis

## 4) Investigation steps (prioritized)
Always output steps in this order (skip if not applicable).
- If the user mentions logs live under `runtime/`, read `references/runtime-logs.md` and suggest concrete grep patterns.
- If the alert is a PHP notice/warning pattern, read `references/php-warning-notice-patterns.md`.
- If the issue looks recurring, consult/update `references/alert-case-library.md`.


1. **确认影响面**：是否影响用户主流程/功能不可用？是否只在 dev？是否测试接口？
2. **定位出错点**：直接打开 `file:line` 看取值来源/入参/分支（特别是数组取值、Mongo/ES 返回结构）。
3. **区分“告警升级” vs “真实致命”**：
   - 若是 `Type=8`：重点排查数据缺字段 + 兜底（`??/isset`）
   - 检查是否存在 `set_error_handler` 将 notice/warning 转异常，或返回值导致 PHP 默认输出污染响应
4. **对齐 runtime 日志**（你们目前日志在 `runtime/`）：
   - 按 `Seen` 时间窗检索（first~last）
   - 若有 `request_id/trace_id`，优先用它串联
   - 关注：同一 fingerprint 是否对应同一入参/同一机器
5. **校验入参/数据**：必填字段、类型、长度、枚举值；上游字段名变更；Mongo/ES 文档缺字段。
6. **检查依赖**：DB/Redis/HTTP 下游超时、连接错误、返回码异常。
7. **对比变更**：first_seen~last_seen 期间是否有发版/配置变更。

Prefer concrete file paths/grep patterns for runtime logs when possible.

## 5) Mitigation
Provide 1-3 safe mitigations, e.g.
- guard test endpoint behind env / auth
- downgrade alerting for known test alerts (fingerprint allowlist)
- add input validation to avoid unhandled exceptions

## 6) Code hardening & optimization suggestions
For PHP/Phalcon controllers and alerting:
- validate params early; return structured error
- for `Undefined index/Undefined variable` in loops: prefer business-side fixes (`??`, `isset`, `intval` default) to eliminate noise
- if upgrading error levels / enabling TG alerts:
  - `set_error_handler` should **return `true`** for notice/warning to avoid PHP default output contaminating JSON responses
  - be careful when combining `set_error_handler` + `register_shutdown_function`: may double-report; keep fatal reporting in shutdown, warn/notice in runtime; add per-request dedupe for foreach spam
- add try/catch at boundary to enrich logs (request_id, fingerprint)
- avoid throwing generic Exception for expected validation failures
- ensure test endpoints disabled in prod
- optionally include a **code context snippet** (±15 lines) in alerts for faster diagnosis, but keep it disabled by default and apply redaction + length limits

## Temporary code-context workflow (only when @mentioned)

When the user wants code context **only for the current analysis**:
1. Prefer the **production-side snippet already included in the TG alert** (because local code may not match prod).
2. Keep alerting system default: `alert.include_code_context=0` and only enable it temporarily when needed (for example via a request header/param on a test endpoint, or a short-lived config flag).
3. Accept either of these inputs:
   - A "Code(±15):" (or "Code") snippet already pasted into the alert
   - If snippet is missing: ask the user to paste the surrounding lines from the **same environment that threw the exception**.

Fallback (only if prod code is accessible locally and matches): use the bundled script:

```bash
php skills/tg-alert-triage/scripts/extract_code_context.php /abs/path/to/File.php 56 15
```

## Output template (recommended)
Return sections in this exact order:
1) 摘要
2) 关键信息(从告警提取)
3) 初步诊断(Top 3 假设)
4) 排查步骤(按优先级)
5) 临时缓解方案
6) 代码/配置优化建议
