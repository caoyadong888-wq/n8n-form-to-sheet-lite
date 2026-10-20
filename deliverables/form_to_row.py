#!/usr/bin/env python3
"""Map a form payload to one sheet row and optionally append a CSV file.

The check below is a pack check. It is not a claim about HTML, RFC 5322, or
the Google Sheets API. Webhook JSON shape differs by n8n version — if `body`
is a JSON object, this helper uses it. Check upstream docs for your Webhook
node.

Standard library only. No network.
"""

from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COLUMNS = ["received_at", "name", "email", "topic", "message", "company"]
TOPICS = ("question", "request", "incident")
MAX_NAME = 120
MAX_COMPANY = 120
MAX_MESSAGE = 2000
MAX_EMAIL = 254


def parse_time(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_now(value: str | None) -> str:
    if not value:
        return format_time(datetime.now(timezone.utc))
    parsed = parse_time(value)
    if parsed is None:
        raise ValueError(f"now is not a timestamp this pack accepts: {value}")
    return format_time(parsed)


def unwrap_payload(document: Any) -> Any:
    """Use document['body'] when it is an object. Otherwise use document."""
    if isinstance(document, dict) and isinstance(document.get("body"), dict):
        return document["body"]
    return document


def valid_email(value: str) -> bool:
    if len(value) > MAX_EMAIL or any(char.isspace() for char in value):
        return False
    if value.count("@") != 1:
        return False
    local, domain = value.split("@")
    if not local or not domain or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False
    labels = domain.split(".")
    for label in labels:
        if not label or label.startswith("-") or label.endswith("-"):
            return False
    tld = labels[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False
    return True


def empty_row(received_at: str) -> dict[str, str]:
    row = {column: "" for column in COLUMNS}
    row["received_at"] = received_at
    return row


def map_payload(document: Any, now: str) -> dict[str, Any]:
    received_at = normalize_now(now)
    payload = unwrap_payload(document)
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "status": "invalid",
            "errors": ["payload"],
            "ignored": [],
            "row": None,
        }
    errors: list[str] = []
    name = str(payload.get("name") or "").strip()
    if not name or len(name) > MAX_NAME or any(char in name for char in "\r\n"):
        errors.append("name")
    email = str(payload.get("email") or "").strip()
    if not valid_email(email):
        errors.append("email")
    topic_raw = str(payload.get("topic") or "").strip()
    topic = topic_raw.casefold()
    if topic not in TOPICS:
        errors.append("topic")
    message = str(payload.get("message") if payload.get("message") is not None else "").strip()
    if not message or len(message) > MAX_MESSAGE:
        errors.append("message")
    company = str(payload.get("company") or "").strip()
    if len(company) > MAX_COMPANY or any(char in company for char in "\r\n"):
        errors.append("company")
    # received_at is set by this helper from --now. A client-supplied value is ignored.
    ignored = sorted(
        key for key in payload.keys() if key not in {"name", "email", "topic", "message", "company"}
    )
    if errors:
        return {
            "ok": False,
            "status": "invalid",
            "errors": errors,
            "ignored": ignored,
            "row": None,
        }
    row = {
        "received_at": received_at,
        "name": name,
        "email": email,
        "topic": topic,
        "message": message,
        "company": company,
    }
    return {
        "ok": True,
        "status": "valid",
        "errors": [],
        "ignored": ignored,
        "row": row,
    }


def csv_line(row: dict[str, str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="")
    writer.writerow([row[column] for column in COLUMNS])
    return buffer.getvalue()


def render_text(result: dict[str, Any]) -> str:
    if not result["ok"]:
        errors = ",".join(result["errors"]) or "(none)"
        ignored = ",".join(result["ignored"]) or "(none)"
        return (
            "form row\n"
            "status: invalid\n"
            f"errors: {errors}\n"
            f"ignored: {ignored}\n"
        )
    row = result["row"]
    ignored = ",".join(result["ignored"]) or "(none)"
    lines = [
        "form row",
        "status: valid",
        f"received_at: {row['received_at']}",
        f"name: {row['name']}",
        f"email: {row['email']}",
        f"topic: {row['topic']}",
        f"message: {row['message']}",
        f"company: {row['company']}",
        f"ignored: {ignored}",
        "csv_header: " + ",".join(COLUMNS),
        "csv_line: " + csv_line(row),
    ]
    return "\n".join(lines) + "\n"


def append_csv(path: Path, row: dict[str, str]) -> int:
    if path.exists() and path.is_dir():
        raise ValueError(f"csv path is a directory: {path}")
    if path.parent and not path.parent.exists():
        raise ValueError(f"csv directory does not exist: {path.parent}")
    new_file = (not path.exists()) or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if new_file:
            writer.writerow(COLUMNS)
        writer.writerow([row[column] for column in COLUMNS])
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0] != COLUMNS:
        raise ValueError("csv header does not match the pack columns")
    return len(rows) - 1


def load_document_from_args(args: argparse.Namespace) -> Any:
    if bool(args.payload) == bool(args.payload_b64):
        raise ValueError("pass exactly one of --payload or --payload-b64")
    if args.payload:
        return json.loads(Path(args.payload).read_text(encoding="utf-8"))
    try:
        raw = base64.b64decode(args.payload_b64.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("payload-b64 is not valid base64") from exc
    return json.loads(raw.decode("utf-8"))


def emit(result: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(render_text(result))


def command_map(args: argparse.Namespace) -> int:
    try:
        document = load_document_from_args(args)
        result = map_payload(document, args.now)
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    emit(result, args.format)
    return 0 if result["ok"] else 2


def command_append_csv(args: argparse.Namespace) -> int:
    try:
        document = load_document_from_args(args)
        result = map_payload(document, args.now)
        if not result["ok"]:
            emit(result, "text")
            return 2
        data_rows = append_csv(Path(args.csv), result["row"])
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    sys.stdout.write(
        "form csv\n"
        "status: appended\n"
        f"path: {args.csv}\n"
        f"data_rows: {data_rows}\n"
        f"received_at: {result['row']['received_at']}\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Map a form payload to a row.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--payload", help="path to a JSON payload or webhook envelope")
        target.add_argument("--payload-b64", help="base64 of that JSON")
        target.add_argument("--now", help="UTC timestamp stored as received_at")

    mapper = sub.add_parser("map", help="validate and print the row")
    add_common(mapper)
    mapper.add_argument("--format", choices=("text", "json"), default="text")
    mapper.set_defaults(func=command_map)

    validate = sub.add_parser("validate", help="same as map; used by the workflow")
    add_common(validate)
    validate.add_argument("--format", choices=("text", "json"), default="text")
    validate.set_defaults(func=command_map)

    append = sub.add_parser("append-csv", help="append a valid row to a local CSV file")
    add_common(append)
    append.add_argument("--csv", required=True)
    append.set_defaults(func=command_append_csv)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
