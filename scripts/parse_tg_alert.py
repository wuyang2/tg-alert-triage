#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse a TG-style alert text into structured JSON.

This is a best-effort parser for alerts formatted like:
【env/app】异常持续发生 x15
Where：POST /path (Module/controller/action)
Error：message
Params：{...}
Loc：File.php:56
Host：HOST
Seen：first=... last=...
Fingerprint：...
Trace(top10)：
#0 ...
JSON：
{...}

Usage:
  cat alert.txt | python3 scripts/parse_tg_alert.py
"""

import json
import re
import sys
from typing import Any, Dict, Optional


def _strip(s: str) -> str:
    return s.strip(" \t\r\n")


def find_block(text: str, start_label: str, end_label_prefixes: list) -> Optional[str]:
    """Return substring after a standalone start_label line until before any end label prefix line.

    end_label_prefixes should be items like "Loc：", "Host：" (prefix match, not full-line match).
    """
    # locate start_label as a standalone line
    m = re.search(rf"^{re.escape(start_label)}\s*$", text, flags=re.M)
    if not m:
        return None
    start = m.end()

    # find next end label (prefix match at line start)
    end = len(text)
    for lab in end_label_prefixes:
        mm = re.search(rf"^{re.escape(lab)}", text[start:], flags=re.M)
        if mm:
            end = min(end, start + mm.start())

    return text[start:end].strip("\n")


def main() -> int:
    raw = sys.stdin.read()
    text = raw.replace("\r\n", "\n")

    out: Dict[str, Any] = {
        "raw": raw,
        "title": None,
        "env": None,
        "app": None,
        "count": None,
        "where": {},
        "error": None,
        "loc": {},
        "host": None,
        "seen": {},
        "fingerprint": None,
        "trace": [],
        "json": None,
        "params": None,
    }

    # Title like: 【dev/yc114】异常持续发生 x15
    m = re.search(r"^【([^/\]]+)/([^\]]+)】.*?x(\d+)\s*$", text, flags=re.M)
    if m:
        out["env"], out["app"], out["count"] = m.group(1), m.group(2), int(m.group(3))
        out["title"] = _strip(m.group(0))

    # Where：POST /api/server/alertTest (Api/server/alertTest)
    m = re.search(r"^Where：\s*(\w+)\s+([^\s]+)\s*(?:\(([^)]+)\))?\s*$", text, flags=re.M)
    if m:
        out["where"] = {"method": m.group(1), "uri": m.group(2), "route": m.group(3)}

    # Error：...
    m = re.search(r"^Error：\s*(.+?)\s*$", text, flags=re.M)
    if m:
        out["error"] = m.group(1)

    # Loc：ServerController.php:56
    m = re.search(r"^Loc：\s*([^:]+):(\d+)\s*$", text, flags=re.M)
    if m:
        out["loc"] = {"file": m.group(1), "line": int(m.group(2))}

    # Host：...
    m = re.search(r"^Host：\s*(.+?)\s*$", text, flags=re.M)
    if m:
        out["host"] = m.group(1)

    # Seen：first=... last=...
    m = re.search(r"^Seen：\s*first=(.+?)\s+last=(.+?)\s*$", text, flags=re.M)
    if m:
        out["seen"] = {"first": m.group(1), "last": m.group(2)}

    # Fingerprint：...
    m = re.search(r"^Fingerprint：\s*(\w+)\s*$", text, flags=re.M)
    if m:
        out["fingerprint"] = m.group(1)

    # Params block: after 'Params：' until 'Loc：' line
    params_block = find_block(text, "Params：", ["Loc：", "Host：", "Seen：", "Fingerprint：", "Trace(top10)：", "JSON："])
    if params_block:
        # try parse JSON-like content
        candidate = params_block.strip()
        try:
            out["params"] = json.loads(candidate)
        except Exception:
            out["params"] = candidate

    # Trace block: after 'Trace(top10)：' until 'JSON：'
    trace_block = find_block(text, "Trace(top10)：", ["JSON："])
    if trace_block:
        out["trace"] = [line for line in trace_block.split("\n") if _strip(line)]

    # JSON block: after 'JSON：' to end
    json_block = find_block(text, "JSON：", [])
    if json_block:
        candidate = json_block.strip()
        try:
            out["json"] = json.loads(candidate)
        except Exception:
            out["json"] = candidate

    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
