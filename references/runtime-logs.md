# runtime 日志排查速查（PHP/Phalcon 常见）

> 目标：从告警的时间窗 / request_id / endpoint，快速在 runtime/ 下定位相关日志。

## 常见目录（按项目不同可能变化）
- `runtime/logs/`
- `app/runtime/logs/`
- `runtime/`

## 常用检索（grep / ripgrep）

> 你们是 `runtime/logs/YYYY-MM-DD.log` 按天：优先只搜当天文件，速度更快、噪音更少。

### 1) 先定位当天日志文件
```bash
ls -lah runtime/logs | tail
# 例如：runtime/logs/2026-03-18.log
```

### 2) 按接口 URI / action（推荐）
```bash
rg -n "/api/server/alertTest" runtime/logs/2026-03-18.log -S
rg -n "ServerController" runtime/logs/2026-03-18.log -S
rg -n "alertTestAction" runtime/logs/2026-03-18.log -S
```

### 3) 按时间窗（Seen first~last）
- 先用 `Seen` 里的日期选择日志文件（可能跨天就搜多个文件）。
- 再用时间字符串（例如 `10:16`）+ 关键字做二次过滤。

示例：
```bash
rg -n "10:16" runtime/logs/2026-03-18.log -S
rg -n "TG报警测试-普通异常" runtime/logs/2026-03-18.log -S
```

### 4) 按 request_id / trace_id
```bash
rg -n "request_id" runtime/logs/2026-03-18.log -S
rg -n "trace_id" runtime/logs/2026-03-18.log -S
# 如果你知道具体值：
rg -n "request_id=zzzz" runtime/logs/2026-03-18.log -S
```

### 5) 按 fingerprint
```bash
rg -n "929219d435630329ac60ddfdda4a3cf6" runtime/logs/2026-03-18.log -S
```

## 建议日志字段（后续可优化）
- request_id / trace_id
- env/app/host
- method/uri
- exception class/message/file/line
- fingerprint
- params（注意脱敏）
