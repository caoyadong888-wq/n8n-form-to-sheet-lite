# n8n Webhook Form to Sheet (Lite)

## English

Map one local JSON form body to a row, or append that row to a CSV file. This subset does not include the importable n8n workflow, the Google Sheet node, or the webhook credential placeholder.

The check is a pack check: name, email, topic (`question`, `request`, or `incident`), and message are required. `company` is optional. Addresses in the sample use example.com.

### Deliverables

- `deliverables/form_to_row.py` — validate a payload and map it to a row
- `deliverables/FIELDS.md` — English and Chinese field rules
- `examples/form-payload.json` — one valid form body
- `examples/form-invalid.json` — a body the helper rejects
- `examples/expected-row.json` — the row for the valid body at a fixed time
- `examples/expected-row.csv` — that row as CSV

### Quick start

```bash
python3 deliverables/form_to_row.py map \
  --payload examples/form-payload.json \
  --now 2026-04-02T12:00:00Z
```

Expect `status: valid` and `email: ada@example.com`. The printed `csv_line` matches `examples/expected-row.csv` without the header.

Requires Python 3.9 or newer. No third-party packages and no network.

## 中文

把一份本地 JSON 表单映射成一行，或把这一行追加到 CSV。精简版不包含可导入的 n8n 工作流、Google Sheet 节点和 webhook 凭据占位符。

检查规则是本包自己的：`name`、`email`、`topic`（`question`、`request` 或 `incident`）和 `message` 必填。`company` 可选。示例地址使用 example.com。

### 交付文件

- `deliverables/form_to_row.py`
- `deliverables/FIELDS.md`
- `examples/form-payload.json`
- `examples/form-invalid.json`
- `examples/expected-row.json`
- `examples/expected-row.csv`

### 快速开始

```bash
python3 deliverables/form_to_row.py map \
  --payload examples/form-payload.json \
  --now 2026-04-02T12:00:00Z
```

预期 `status: valid` 和 `email: ada@example.com`。打印出的 `csv_line` 与 `examples/expected-row.csv` 去掉表头后的那一行相同。

需要 Python 3.9 或更高版本。无第三方包，也不需要网络。

Full version: GUMROAD_URL
