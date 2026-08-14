#!/usr/bin/env python3
"""Monitor Service - single-file Flask app.

Implements:
  POST /monitor/commands

It lists running processes by reading from /proc (no external commands required).
Also provides a minimal web UI at GET /.
"""

from __future__ import annotations

import json
import os
import pwd
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, render_template_string


app = Flask(__name__)


# -----------------------------
# Utilities
# -----------------------------

def _error(code: int, message: str, http_status: int) -> Tuple[Any, int]:
    """Return an Error object payload with the given HTTP status."""
    return jsonify({"code": int(code), "message": str(message)}), int(http_status)


def _safe_read_text(path: str, max_bytes: int = 1_000_000) -> str:
    """Read a text file with reasonable caps; return empty string on failure."""
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        # /proc files are usually UTF-8-ish but can contain arbitrary bytes
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _read_cmdline(pid: int) -> str:
    """Return the process command line (args joined by spaces).

    Uses /proc/<pid>/cmdline (NUL-separated). Falls back to /proc/<pid>/comm.
    """
    cmd_path = f"/proc/{pid}/cmdline"
    try:
        with open(cmd_path, "rb") as f:
            raw = f.read(4096)
        if raw:
            parts = [p.decode("utf-8", errors="replace") for p in raw.split(b"\x00") if p]
            cmd = " ".join(parts).strip()
            if cmd:
                return cmd
    except Exception:
        pass

    comm = _safe_read_text(f"/proc/{pid}/comm", max_bytes=256).strip()
    return comm


def _read_user(pid: int) -> str:
    """Best-effort username for process owner."""
    try:
        st = os.stat(f"/proc/{pid}")
        return pwd.getpwuid(st.st_uid).pw_name
    except Exception:
        return "?"


def _read_stat(pid: int) -> Dict[str, Any]:
    """Best-effort parse of /proc/<pid>/stat for some ps-like fields."""
    stat_text = _safe_read_text(f"/proc/{pid}/stat", max_bytes=4096).strip()
    if not stat_text:
        return {}

    # /proc/<pid>/stat: pid (comm) state ppid ...
    # comm can contain spaces, wrapped in parentheses. We'll parse accordingly.
    # Find the last ')' after the first '('.
    try:
        lpar = stat_text.find("(")
        rpar = stat_text.rfind(")")
        if lpar == -1 or rpar == -1 or rpar <= lpar:
            return {}
        after = stat_text[rpar + 1 :].strip().split()
        state = after[0] if after else "?"
        ppid = int(after[1]) if len(after) > 1 else None
        return {"state": state, "ppid": ppid}
    except Exception:
        return {}


def _list_pids() -> List[int]:
    """Return list of PIDs from /proc."""
    pids: List[int] = []
    try:
        for name in os.listdir("/proc"):
            if name.isdigit():
                try:
                    pids.append(int(name))
                except ValueError:
                    continue
    except Exception:
        return []
    return sorted(pids)


def _build_process_string(pid: int, cmdline: str, filter_flags: str) -> str:
    """Create a ps-like single-line representation.

    We support a *very small* subset of ps-style output controlled by filter_flags.
    This is intentionally minimal and does not shell out to `ps`.

    - If filter_flags includes 'u' or resembles 'aux', we include a USER column.
    - Otherwise we output: "PID=<pid>    CMD=<cmdline>".
    """
    flags = (filter_flags or "").strip()
    include_user = ("u" in flags) or ("aux" in flags.replace(" ", ""))

    if include_user:
        user = _read_user(pid)
        st = _read_stat(pid)
        state = st.get("state", "?")
        ppid = st.get("ppid", "?")
        return f"{user}\tPID={pid}\tPPID={ppid}\tSTATE={state}\tCMD={cmdline}".strip()

    return f"PID={pid}\tCMD={cmdline}".strip()


def _validate_payload(payload: Any) -> Tuple[Optional[str], str]:
    """Validate request payload; returns (filter_flags, command_regex) or error."""
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")

    command_regex = payload.get("command_regex")
    if not isinstance(command_regex, str) or not command_regex.strip():
        raise ValueError("'command_regex' is required and must be a non-empty string")

    # Basic hard limits to reduce the chance of pathological regex / abuse.
    if len(command_regex) > 256:
        raise ValueError("'command_regex' is too long (max 256 characters)")

    filter_flags = payload.get("filter_flags")
    if filter_flags is not None and not isinstance(filter_flags, str):
        raise ValueError("'filter_flags' must be a string if provided")

    if isinstance(filter_flags, str) and len(filter_flags) > 64:
        raise ValueError("'filter_flags' is too long (max 64 characters)")

    return filter_flags, command_regex


def _match_processes(command_regex: str, filter_flags: str) -> List[Dict[str, Any]]:
    """Return list of matching processes as API objects."""
    try:
        pattern = re.compile(command_regex)
    except re.error as e:
        raise ValueError(f"Invalid regular expression: {e}")

    results: List[Dict[str, Any]] = []
    for pid in _list_pids():
        cmd = _read_cmdline(pid)
        if not cmd:
            continue
        if pattern.search(cmd):
            results.append(
                {
                    "processId": pid,
                    "processString": _build_process_string(pid, cmd, filter_flags or ""),
                }
            )
    return results


# -----------------------------
# API
# -----------------------------

@app.post("/monitor/commands")
def monitor_commands():
    payload = request.get_json(silent=True)
    if payload is None:
        raw = request.data or b""
        if raw.strip():
            try:
                payload = json.loads(raw.decode("utf-8", errors="replace"))
            except Exception:
                return _error(400, "Invalid JSON body", 400)
        else:
            return _error(400, "Missing JSON body", 400)

    try:
        filter_flags, command_regex = _validate_payload(payload)
        matches = _match_processes(command_regex=command_regex, filter_flags=filter_flags or "")
        return jsonify(matches), 200
    except ValueError as e:
        return _error(400, str(e), 400)
    except Exception:
        return _error(500, "Internal server error", 500)


# -----------------------------
# Minimal web UI
# -----------------------------

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Monitor Service</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;max-width:1000px;margin:40px auto;padding:0 16px;}
    h1{margin:0 0 8px 0;}
    .card{border:1px solid #ddd;border-radius:12px;padding:16px;margin:16px 0;}
    label{display:block;margin:10px 0 6px 0;font-weight:600;}
    input{width:100%;padding:10px;border:1px solid #ccc;border-radius:10px;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;}
    button{padding:10px 14px;border:1px solid #222;background:#222;color:#fff;border-radius:10px;cursor:pointer;}
    button:disabled{opacity:.6;cursor:not-allowed;}
    pre{white-space:pre-wrap;word-break:break-word;background:#f6f6f6;border:1px solid #eee;border-radius:12px;padding:12px;}
    .muted{color:#666;font-size:14px;}
    .row{display:flex;gap:12px;flex-wrap:wrap;}
    .row > div{flex:1 1 320px;}
  </style>
</head>
<body>
  <h1>Monitor Service</h1>
  <p class="muted">Find running processes whose <code>cmdline</code> matches a regular expression (no <code>ps</code> shell-out; uses <code>/proc</code>).</p>

  <div class="card">
    <div class="row">
      <div>
        <label for="command_regex">command_regex (required)</label>
        <input id="command_regex" value="python.*" placeholder="e.g. ps.*" />
      </div>
      <div>
        <label for="filter_flags">filter_flags (optional)</label>
        <input id="filter_flags" value="aux" placeholder="e.g. aux -T" />
      </div>
    </div>
    <div style="margin-top:12px;display:flex;gap:10px;align-items:center;">
      <button id="runBtn" onclick="run()">Search</button>
      <span id="status" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h3 style="margin-top:0;">Results</h3>
    <pre id="out">(click Search)</pre>
  </div>

<script>
async function run(){
  const btn = document.getElementById('runBtn');
  const status = document.getElementById('status');
  const out = document.getElementById('out');
  btn.disabled = true;
  status.textContent = 'Running...';

  const body = {
    command_regex: document.getElementById('command_regex').value,
    filter_flags: document.getElementById('filter_flags').value
  };

  try{
    const res = await fetch('/monitor/commands', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const text = await res.text();
    let obj;
    try{ obj = JSON.parse(text); } catch(e){ obj = text; }

    if(!res.ok){
      out.textContent = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
      status.textContent = 'Error (' + res.status + ')';
    } else {
      out.textContent = JSON.stringify(obj, null, 2);
      status.textContent = 'OK (' + (Array.isArray(obj) ? obj.length : 0) + ' matches)';
    }
  } catch(err){
    out.textContent = String(err);
    status.textContent = 'Network error';
  } finally {
    btn.disabled = false;
    setTimeout(() => { status.textContent = ''; }, 3000);
  }
}
</script>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(INDEX_HTML)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": int(time.time())})


# -----------------------------
# Error handlers
# -----------------------------

@app.errorhandler(404)
def not_found(_):
    return _error(404, "Not found", 404)


@app.errorhandler(405)
def method_not_allowed(_):
    return _error(405, "Method not allowed", 405)


@app.errorhandler(500)
def internal_error(_):
    return _error(500, "Internal server error", 500)


if __name__ == "__main__":
    # Always bind on 0.0.0.0:3000 as required.
    app.run(host="0.0.0.0", port=3000, debug=False)