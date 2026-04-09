# TG Alert Case Library (yc114)

> 用途：沉淀已验证/高复用的告警根因与处理方案。
> 注意：尽量保存“模式 + 结论 + 复盘”，不要保存敏感参数/用户数据。

## Case: PHP Type=8 Notice/Warning escalated to alert

### Symptom
- 告警类型显示 `Type=8 (E_NOTICE/E_WARNING)`
- 常见文案：`Undefined index` / `Undefined variable` / `Trying to access array offset`
- 可能被错误处理器升级为“异常告警”，但本质未必导致进程崩溃

### Likely root causes
1) 业务数据缺字段 / 上游字段变更
2) 入参未校验，数组直接取值
3) error_handler 将 notice/warning 转异常或污染响应（JSON 前输出 warning 文本）

### First checks
- 先确认是否真的 500 / 影响主流程
- 对照同 fingerprint 是否集中在某一类入参/机器/版本

### Fix patterns
- 取值处兜底：`$x['k'] ?? ''` / `isset($x['k'])`
- 入参校验：缺字段直接返回结构化错误
- 若用了 `set_error_handler`��注意返回 `true`，避免默认输出污染响应

---

## Case: Undefined index: name in logging/report service

### Symptom
- 典型：`Undefined index: name` 指向 Report/Log/埋点类 service
- 业务接口可能正常，但告警持续产生

### Likely root causes
- 日志/埋点 payload 里的可选字段被当成必填
- 不同分支组装 payload 不一致（某分支未补齐 name）

### Fix patterns
- 日志侧做“容错兜底”，避免影响主流程
- 同时补齐“缺字段时记录上下文”（不含敏感信息）便于定位来源

---

## Case: Alert spam / duplicated alerts

### Symptom
- 同一 fingerprint 短时间大量重复

### Likely root causes
- 同一请求内循环触发 notice（foreach 内取字段）
- shutdown + runtime handler 重复上报

### Fix patterns
- per-request 去重（fingerprint + file:line）
- 在循环内提前判断/缓存结果，避免每次都触发 notice

---

## Template for new cases
### Case title

#### Symptom

#### Impact

#### Root cause

#### Fix

#### Verification

#### Postmortem
