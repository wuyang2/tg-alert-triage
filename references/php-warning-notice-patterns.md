# PHP Warning/Notice Patterns (for TG alerts)

## Goal
Provide a small, reusable pattern library for the most common PHP notice/warning alerts that show up in Telegram.

## Pattern 1: Undefined index / Undefined variable
### Meaning
数组/变量不存在，直接读取触发 notice/warning。

### Common places
- 参数读取：`$params['x']`
- 组装 payload：`$data['name']`
- 遍历行数据：`foreach ($rows as $r) { $r['k'] }`

### Preferred fix
- 对“可选字段”使用兜底：`$v = $a['k'] ?? null;`
- 对“必填字段”做入口校验并返回结构化错误

### Anti-pattern
- 在深层 service 内随意 throw（会放大影响面）

---

## Pattern 2: Trying to access array offset on value of type null
### Meaning
变量是 null，不是 array，却当数组访问。

### Fix
- 初始化默认结构
- guard：`if (!is_array($x)) { ... }`

---

## Pattern 3: Invalid argument supplied for foreach
### Meaning
`foreach` 的变量不是 array/Traversable。

### Fix
- 确保返回值类型一致（空集合返回 `[]`）
- `foreach (($x ?? []) as $item) { ... }`

---

## Pattern 4: JSON response polluted by warnings
### Symptom
前端报 JSON parse error，但后端接口逻辑看似成功。

### Root cause
- notice/warning 被输出到响应 body 前部

### Fix
- 生产环境关闭 display_errors
- error_handler 对 notice/warning return true
- 统一捕获输出 JSON，不让 PHP 默认输出混进响应

---

## Pattern 5: Notice escalated by custom error handler
### Meaning
notice/warning 本来不致命，但被转换为异常/告警。

### What to do first
- 判断是否影响用户主流程
- 若不影响：优先消噪（兜底/校验），必要时下调告警级别
