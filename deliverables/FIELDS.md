# Fields

Pack checks only. This is not an HTML or RFC 5322 claim.

| Field | Rule |
| --- | --- |
| `name` | Required, 1–120 characters, no line breaks |
| `email` | Required, one `@`, no spaces, dotted domain, at most 254 characters |
| `topic` | `question`, `request`, or `incident` |
| `message` | Required, 1–2000 characters |
| `company` | Optional, at most 120 characters, no line breaks |

`received_at` comes from `--now`. Other keys are ignored, not rejected. Samples use `ada@example.com` and `ops@example.com`.

# 字段

只是本包的检查，不是 HTML 或 RFC 5322 声明。

| 字段 | 规则 |
| --- | --- |
| `name` | 必填，1–120 个字符，不能换行 |
| `email` | 必填，一个 `@`，无空白，域名有点，最多 254 个字符 |
| `topic` | `question`、`request` 或 `incident` |
| `message` | 必填，1–2000 个字符 |
| `company` | 可选，最多 120 个字符，不能换行 |

`received_at` 来自 `--now`。其他键会被忽略，不会因此拒绝。示例使用 `ada@example.com` 和 `ops@example.com`。
