#!/usr/bin/env python3
"""
Klinik Cron Log Monitor — dashboard log run cron Hermes (localhost saja).

Sumber data:
- Output run cron: %LOCALAPPDATA%/hermes/cron/output/442bba7081d8/*.md
- Status job:      %LOCALAPPDATA%/hermes/cron/jobs.json + ticker_heartbeat

Fitur:
- Daftar run (sidebar) + isi run terpilih di panel utama
- Parser: bagian Response diringkas jadi ringkasan bermakna (kartu selesai,
  commit, validasi, peringatan) — bukan dump mentah
- Filter cepat: semua / error & warning / kartu selesai / commit
- Auto-refresh 15 detik, badge run baru
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERMES = Path.home() / "AppData" / "Local" / "hermes"
CRON_DIR = HERMES / "cron"
OUTPUT_DIR = CRON_DIR / "output" / "442bba7081d8"
JOBS_JSON = CRON_DIR / "jobs.json"
HEARTBEAT = CRON_DIR / "ticker_heartbeat"
EXECUTIONS_DB = CRON_DIR / "executions.db"
TRELLO_TOKENS = Path.home() / ".trello-mcp-lite" / "tokens.json"
# List board yang dirender: milik Hermes dan milik agent lain (Codex dll)
TRELLO_LISTS = [
    ("progress hermes", "6adab9beb8a5daffbaf95f6a"),
    ("progress (agent lain)", "6ad7fee5455f933ec728788c"),
]
_board_cache = {"data": None, "at": 0.0}

_cache: dict = {"data": None, "at": 0.0, "sig": None}
_lock = threading.Lock()
TTL = 2  # semi-realtime: data baru paling lambat 2 detik + polling frontend 3 detik


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_runs() -> list[dict]:
    if not OUTPUT_DIR.exists():
        return []
    runs = []
    for f in OUTPUT_DIR.glob("*.md"):
        st = f.stat()
        runs.append({"file": f.name, "mtime": st.st_mtime, "size": st.st_size})
    runs.sort(key=lambda r: r["mtime"], reverse=True)
    return runs


# ---------------- parser laporan run ----------------

CARD_RE = re.compile(r"^#{2,3}\s+(?:Kartu\s*)?(\d+)?[:.]?\s*(.+?)\s*(?:→|->)\s*\*?`?(review|progress)\*?`?\s*$", re.I | re.M)
HEADING_KARTU_RE = re.compile(r"^#{2,3}\s+Kartu\s*(\d+)?\s*[:.]?\s*(.*)$", re.I)
NUM_CARD_RE = re.compile(r"^\s*(?:\*\*)?\s*(\d+)[\.\)]\s+(?:\*\*)([^*]+)\*\*\s*(.*)$")
BULLET_CARD_RE = re.compile(r"^[-•]\s+\*\*([^*]+?)[ \t]*\*\*[ \t]*([^\n]*)$")
LABEL_RE = re.compile(r"[\w\s]+:$")  # "Temuan:", "Fix:", "Catatan:" = label, bukan judul kartu
ARROW_RE = re.compile(r"(?:→|->)\s*\*?`?(review|progress)\b", re.I)
COMMIT_RE = re.compile(r"([0-9a-f]{7,12})")
WARN_PAT = re.compile(r"(⚠️|FAILED|Error|error|gagal|pre-existing|blocked|DILARANG)", re.I)


def parse_cards(body: str) -> list[dict]:
    """Ekstrak entri PER KARTU dari body laporan: judul, status (review/progress),
    SHA commit, dan detail bullet di bawahnya — agar progress terlihat per kartu.

    Format dikenali:
    - Heading "## Kartu 1: Judul" / "## Kartu 1 selesai penuh: #217 Judul"
    - Item bernomor bold "1. **Judul** (`sha` test, `sha` feat)"
    - Bullet "- ..." di bawah kartu jadi detail kartu tersebut.
    """
    cards: list[dict] = []
    cur: dict | None = None

    def close():
        nonlocal cur
        if cur:
            if not cur["to"]:
                joined = " ".join(cur["details"]).lower()
                if "review" in joined:
                    cur["to"] = "review"
                elif "progress" in joined:
                    cur["to"] = "progress"
            seen: list[str] = []
            for x in cur["shas"]:
                if x not in seen:
                    seen.append(x)
            cur["shas"] = seen[:8]
            cards.append(cur)
            cur = None

    lines = body.splitlines()
    for i, raw in enumerate(lines):
        st = raw.strip()
        if re.match(r"^#{1,3}\s", st):
            close()
            hm = HEADING_KARTU_RE.match(st)
            if hm:
                num, rest = hm.group(1), (hm.group(2) or "").strip()
                to_m = ARROW_RE.search(rest)
                to = to_m.group(1).lower() if to_m else None
                idm = re.search(r"#(\d+)", rest)
                idv = idm.group(1) if idm else (num or None)
                # Heading "Kartu" tanpa nomor (mis. "Kartu Kerja Kode + Test")
                # hanya jadi pseudo-kartu jika item berikutnya bukan kartu bernomor.
                if idv is None:
                    nxt = next((l.strip() for l in lines[i + 1:] if l.strip()), "")
                    if NUM_CARD_RE.match(nxt):
                        continue
                title = re.sub(r"^#?\d+\s*", "", rest)
                title = ARROW_RE.sub("", title).strip(" :`-")
                title = re.sub(r"\s*\([`0-9a-f,\s`]+\)\s*$", "", title).strip(" :`-")
                cur = {"id": idv or "?", "title": title or "(tanpa judul)", "to": to,
                       "shas": COMMIT_RE.findall(rest)[:6], "details": []}
            continue
        if not st or st == "---":
            continue
        bm = BULLET_CARD_RE.match(st)
        if bm and not LABEL_RE.search(bm.group(1)):
            close()
            idm = re.search(r"#(\d+)", bm.group(1))
            _t = re.sub(r"\s*\([`0-9a-f,\s`]+\)\s*$", "", bm.group(1)).strip(" :`-")
            cur = {"id": idm.group(1) if idm else "?", "title": _t or bm.group(1).strip(), "to": None,
                   "shas": COMMIT_RE.findall(bm.group(2) or "")[:6], "details": []}
            continue
        nm = NUM_CARD_RE.match(st)
        if nm:
            close()
            _t = re.sub(r"\s*\([`0-9a-f,\s`]+\)\s*$", "", nm.group(2)).strip(" :`-")
            cur = {"id": nm.group(1), "title": _t or nm.group(2).strip(), "to": None,
                   "shas": [], "details": []}
            cur["shas"] += COMMIT_RE.findall(nm.group(3) or "")[:6]
            cur["shas"] += COMMIT_RE.findall(nm.group(2))[:6]
            continue
        if cur is not None:
            t = st.lstrip("-• ").strip() if st.startswith(("-", "•")) else st
            t = t.strip()
            if t:
                cur["details"].append(t[:240])
                if len(cur["shas"]) < 8:
                    cur["shas"] += [x for x in COMMIT_RE.findall(t) if x not in cur["shas"]][:2]
    close()
    return cards


def parse_run(text: str) -> dict:
    # Bagian Response = setelah header "## Response" (fallback: seluruh teks)
    m = re.search(r"^##\s*Response\s*$", text, re.M)
    body = text[m.end():] if m else text

    # Kartu yang disebut dengan status (parser lama, fallback)
    cards = []
    for cm in CARD_RE.finditer(text):
        cards.append({"id": cm.group(1) or "?", "title": cm.group(2).strip(), "to": cm.group(3).lower()})

    # Commit SHA yang disebut
    shas = []
    for sm in COMMIT_RE.finditer(body):
        sha = sm.group(1)
        if sha not in shas:
            shas.append(sha)

    # Baris-baris bernilai: bullet dengan kata kunci
    highlights = []
    for line in body.splitlines():
        s = line.strip().lstrip("-• ").strip()
        if not s or len(s) < 12:
            continue
        if s.startswith("#"):
            continue
        if re.match(r"^\*\*", s) or s.startswith("Kartu") or "review" in s.lower()[:40]:
            highlights.append(s[:220])

    warnings = []
    # Warning hanya dari bagian Response (bukan kutipan prompt/aturan worker)
    resp_m2 = re.search(r"^##\s*Response\s*$", text, re.M)
    scope_w = text[resp_m2.end():] if resp_m2 else text
    for line in scope_w.splitlines():
        s = line.strip()
        if s and WARN_PAT.search(s) and not s.startswith("#"):
            # buang baris prompt/boilerplate yang panjangnya tidak wajar
            if len(s) < 300:
                warnings.append(s[:260])

    silent = False
    failure = False
    # Token hanya berlaku bila di posisi jawaban (setelah header ## Response),
    # bukan di dalam kutipan prompt run sebelumnya.
    resp_m = re.search(r"^##\s*Response\s*$", text, re.M)
    scope = text[resp_m.end():] if resp_m else ""
    scope_head = scope[:600]
    if "[SILENT]" in scope_head and "respond with exactly" not in scope_head:
        silent = True
    if "[CRON_FAILURE]" in scope_head:
        failure = True

    # Ringkasan 1 baris: baris pertama setelah "# Ringkasan" atau kalimat pertama Response
    summary = ""
    sm = re.search(r"#\s*Ringkasan[^\n]*\n+\s*\*?\*?([^\n*]+)", body)
    if sm:
        summary = sm.group(1).strip()
    else:
        for line in body.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("**") and len(s) > 20:
                summary = s[:200]
                break

    # Parser per kartu (judul + SHA + detail) — utama
    rich_cards = parse_cards(body)
    if rich_cards:
        # gabungkan status dari parser lama bila rich tidak punya
        by_norm = {re.sub(r"[^a-z0-9]", "", c["title"].lower())[:40]: c.get("to") for c in cards}
        # status default dari ringkasan run (mis. "14 kartu dituntaskan ke `review`")
        run_status = "review" if (re.search(r"kartu[^.\n]*review", summary, re.I) or re.search(r"kartu[^.\n]{0,40}review", body[:400], re.I)) else None
        for c in rich_cards:
            if not c["to"]:
                k = re.sub(r"[^a-z0-9]", "", c["title"].lower())[:40]
                c["to"] = by_norm.get(k) or ("review" if "review" in " ".join(c["details"]).lower() else None) or run_status
        cards = rich_cards

    return {
        "summary": summary,
        "cards": cards[:20],
        "shas": shas[:10],
        "highlights": highlights[:10],
        "warnings": warnings[:8],
        "silent": silent,
        "failure": failure,
        "chars": len(text),
    }


def read_live_activity() -> list[dict]:
    """Baca tool call terakhir cron worker DENGAN DETAIL ARGUMEN dari
    state.db (tabel messages, session cron terakhir): perintah terminal
    apa, file apa yang dibaca/patched."""
    state_db = Path.home() / "AppData/Local/hermes/state.db"
    if not state_db.exists():
        return []
    try:
        db = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True, timeout=3)
        cur = db.cursor()
        # session cron terakhir (source='cron', urut pesan terbaru)
        row = cur.execute(
            "SELECT id FROM sessions WHERE source='cron' ORDER BY last_activity_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            db.close()
            return []
        sid = row[0]
        rows = cur.execute(
            "SELECT role, tool_name, tool_calls, content, timestamp FROM messages "
            "WHERE session_id=? AND (tool_calls IS NOT NULL OR role='assistant') "
            "ORDER BY id DESC LIMIT 60",
            (sid,),
        ).fetchall()
        db.close()
    except Exception:
        return []

    calls = []
    for role, tname, tcalls, content, ts in rows:
        t = float(ts) if isinstance(ts, (int, float)) else time.time()
        time_s = datetime.fromtimestamp(t).strftime("%H:%M:%S")
        if role == "assistant" and tcalls:
            try:
                parsed = json.loads(tcalls) if isinstance(tcalls, str) else tcalls
                if isinstance(parsed, list):
                    for call in parsed:
                        fn = call.get("function", {})
                        name = fn.get("name", "?")
                        try:
                            args = json.loads(fn.get("arguments", "{}"))
                        except Exception:
                            args = {}
                        detail = _summarize_args(name, args)
                        calls.append({"time": time_s, "tool": name, "detail": detail, "dur": None, "kind": "call"})
            except Exception:
                pass
        elif role == "tool" and tname:
            calls.append({"time": time_s, "tool": tname, "detail": "↳ selesai", "dur": None, "kind": "done"})
    # urut kronologis, ambil 40 terakhir
    calls.reverse()
    return calls[-40:]


def _summarize_args(name: str, args: dict) -> str:
    """Ringkas argumen tool jadi 1 baris bermakna."""
    if name == "terminal":
        return (args.get("command") or "")[:160]
    if name in ("read_file", "write_file"):
        return f"{args.get('path', '')}"
    if name == "patch":
        return f"{args.get('path', '')}"
    if name == "execute_code":
        code = (args.get("code") or "").replace("\n", " ")
        return code[:160]
    if name == "skill_view":
        return f"skill: {args.get('name', '')}"
    if "trello" in name:
        return f"{args.get('method', '')} {args.get('endpoint', '')}"
    if name == "grep" or name == "search_files":
        return f"pattern: {args.get('pattern', '')} path: {args.get('path', '')}"
    return json.dumps(args, ensure_ascii=False)[:160]


def read_execution() -> dict:
    """Baca eksekusi terakhir job worker dari executions.db (sumber kebenaran
    status running/completed/failed — bebas dari agent lain)."""
    if not EXECUTIONS_DB.exists():
        return {}
    try:
        db = sqlite3.connect(f"file:{EXECUTIONS_DB}?mode=ro", uri=True, timeout=3)
        cur = db.cursor()
        cur.execute(
            "SELECT status, started_at, finished_at, progress_at, error FROM executions "
            "WHERE job_id='442bba7081d8' ORDER BY started_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        db.close()
        if not row:
            return {}
        status, started, finished, progress, error = row
        return {
            "status": status,
            "started": str(started)[11:19] if started else "-",
            "finished": str(finished)[11:19] if finished else None,
            "progress_age": _iso_age(progress),
            "error": (str(error)[:200] if error else None),
        }
    except Exception:
        return {}


def _iso_age(value) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        return f"{time.time() - dt.timestamp():.0f}"
    except Exception:
        return None


def read_board_cards() -> dict:
    """Kartu aktif per list dari Trello (semua agent, bukan hanya Hermes).
    Cache 30 detik agar hemat rate limit Trello."""
    if _board_cache["data"] is not None and time.time() - _board_cache["at"] < 30:
        return _board_cache["data"]
    import urllib.request
    import urllib.parse
    out: dict = {"lists": [], "error": None}
    try:
        acc = json.loads(TRELLO_TOKENS.read_text(encoding="utf-8"))["haidi"]
        key, token = acc["apiKey"], acc["token"]
        for name, lid in TRELLO_LISTS:
            q = urllib.parse.urlencode({
                "key": key, "token": token,
                "fields": "name,idShort,badges,dateLastActivity,shortUrl,labels",
                "limit": "60",
            })
            req = urllib.request.Request(f"https://api.trello.com/1/lists/{lid}/cards?{q}")
            with urllib.request.urlopen(req, timeout=10) as r:
                cards = json.load(r)
            out["lists"].append({
                "name": name,
                "cards": [{
                    "name": c.get("name", ""),
                    "idShort": c.get("idShort"),
                    "url": c.get("shortUrl"),
                    "ac": f"{(c.get('badges') or {}).get('checkItemsChecked', 0)}/{(c.get('badges') or {}).get('checkItems', 0)}",
                    "age_min": int((time.time() - datetime.fromisoformat(c["dateLastActivity"].replace("Z", "+00:00")).timestamp()) / 60) if c.get("dateLastActivity") else None,
                    "labels": [{"name": l.get("name", ""), "color": l.get("color") or "gray"} for l in (c.get("labels") or [])][:4],
                } for c in cards],
            })
    except Exception as e:
        out["error"] = str(e)[:150]
    _board_cache["data"] = out
    _board_cache["at"] = time.time()
    return out


def collect(force: bool = False) -> dict:
    runs = list_runs()
    sig = tuple((r["file"], r["mtime"]) for r in runs[:8])
    with _lock:
        if not force and _cache["data"] is not None and _cache["sig"] == sig and time.time() - _cache["at"] < TTL:
            return _cache["data"]

    jobs = read_json(JOBS_JSON) or {}
    jl = jobs.get("jobs", []) if isinstance(jobs, dict) else []
    job = jl[0] if jl else {}

    hb = ""
    if HEARTBEAT.exists():
        try:
            ts = float(HEARTBEAT.read_text().split()[0])
            hb = f"{time.time() - ts:.0f}"
        except Exception:
            pass

    items = []
    for r in runs[:30]:
        try:
            text = (OUTPUT_DIR / r["file"]).read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""
        parsed = parse_run(text)
        dt = datetime.fromtimestamp(r["mtime"])
        items.append({
            "file": r["file"],
            "time": dt.strftime("%H:%M:%S"),
            "date": dt.strftime("%Y-%m-%d"),
            "ts": r["mtime"],
            "size_kb": round(r["size"] / 1024, 1),
            **parsed,
        })

    data = {
        "now": datetime.now().strftime("%H:%M:%S"),
        "execution": read_execution(),
        "activity": read_live_activity(),
        "board": read_board_cards(),
        "job": {
            "name": job.get("name", "-"),
            "schedule": job.get("schedule", "-"),
            "enabled": job.get("enabled", False),
            "state": job.get("state", "-"),
            "last_status": job.get("last_status", "-"),
            "last_run": str(job.get("last_run_at", "-"))[11:19],
            "next_run": str(job.get("next_run_at", "-"))[11:19],
            "last_error": job.get("last_error"),
        },
        "heartbeat_sec": hb,
        "runs": items,
    }
    with _lock:
        _cache["data"] = data
        _cache["sig"] = sig
        _cache["at"] = time.time()
    return data


def get_data():
    try:
        return collect()
    except Exception as e:
        return {"error": str(e), "runs": [], "job": {}, "now": datetime.now().strftime("%H:%M:%S")}


HTML = r"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Cron Log — Klinik Worker</title>
<style>
  :root{
    --bg:#0b0e14;--panel:#11151d;--panel2:#171d29;--border:#232a36;--text:#e2e8f0;
    --muted:#7d8590;--accent:#4c9aff;--green:#3fb950;--red:#f85149;--yellow:#d29922;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font:13.5px/1.55 "Segoe UI",system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
  header{display:flex;align-items:center;gap:12px;padding:12px 18px;border-bottom:1px solid var(--border);flex:none}
  h1{font-size:15px;font-weight:600}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.8s infinite}
  .dot.off{background:var(--red);animation:none}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
  .hb{color:var(--muted);font-size:12px}
  .spacer{flex:1}
  .filters{display:flex;gap:6px}
  .filters button{background:transparent;border:1px solid var(--border);color:var(--muted);padding:5px 12px;border-radius:7px;font-size:12px;cursor:pointer}
  .filters button.on{color:var(--text);border-color:var(--muted);background:var(--panel2)}
  main{flex:1;display:flex;flex-direction:column;overflow:hidden}
  aside{border-right:1px solid var(--border);overflow-y:auto;padding:8px}
  .run{border-radius:8px;padding:8px 11px;margin-bottom:2px;cursor:pointer}
  .run:hover{background:var(--panel)}
  .run.sel{background:var(--panel2)}
  .run .t{display:flex;justify-content:space-between;align-items:baseline;font-variant-numeric:tabular-nums}
  .run .t b{font-size:13px;font-weight:600}
  .run .kb{color:var(--muted);font-size:11px}
  .run .s{color:var(--muted);font-size:12px;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .chips{display:flex;gap:5px;margin-top:4px;flex-wrap:wrap}
  .chip{font-size:10.5px;padding:1px 8px;border-radius:999px;font-weight:600}
  .chip.g{background:rgba(63,185,80,.14);color:var(--green)}
  .chip.r{background:rgba(248,81,73,.14);color:var(--red)}
  .chip.y{background:rgba(210,153,34,.14);color:var(--yellow)}
  .chip.n{background:var(--panel2);color:var(--muted)}
  section{overflow-y:auto;padding:18px 22px}
  .head{display:flex;align-items:baseline;gap:12px;margin-bottom:14px;flex-wrap:wrap}
  .head h2{font-size:16px}
  .head .m{color:var(--muted);font-size:12px}
  .block{margin-bottom:18px}
  .block h3{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin-bottom:8px}
  .cards{display:flex;flex-direction:column;gap:4px}
  .crow{display:flex;gap:10px;align-items:baseline;padding:6px 10px;border-radius:7px;background:var(--panel);flex-wrap:wrap}
  .crow .id{color:var(--accent);font-weight:600;flex:none;min-width:36px}
  .crow .ttl{flex:1;min-width:200px}
  .crow .to{flex:none;font-size:11px}
  .crow .shas{flex-basis:100%;display:flex;gap:5px;flex-wrap:wrap;padding-left:46px}
  .sha{font:11px Consolas,monospace;background:var(--panel2);border-radius:5px;padding:1px 7px;color:var(--muted);text-decoration:none}
  .sha:hover{color:var(--accent);outline:1px solid var(--border)}
  .dtoggle{flex:none;font-size:11px;color:var(--accent);background:none;border:none;cursor:pointer;padding:0}
  .cdetail{flex-basis:100%;display:none;padding:2px 0 2px 46px;color:var(--muted);font-size:12px}
  .cdetail.open{display:block}
  .cdetail li{margin:2px 0 2px 14px}
  .hl li,.warn li{margin:3px 0 3px 16px}
  .warn li{color:var(--yellow)}
  .raw{white-space:pre-wrap;font:12px/1.6 Consolas,monospace;color:#b6c2cf;background:var(--panel);border-radius:8px;padding:14px;max-height:420px;overflow-y:auto}
  .empty{color:var(--muted);padding:30px;text-align:center}
  #rawbtn{background:none;border:none;color:var(--accent);cursor:pointer;font-size:12px;padding:0}
  .exec{display:flex;align-items:center;gap:9px;padding:7px 12px;border-radius:8px;background:var(--panel);font-size:12.5px}
  .exec.running{outline:1px solid rgba(63,185,80,.4)}
  .exec .st{font-weight:700;font-size:11px;padding:1px 9px;border-radius:999px}
  .exec .st.running{background:rgba(63,185,80,.14);color:var(--green)}
  .exec .st.completed{background:rgba(76,154,255,.14);color:var(--accent)}
  .exec .st.failed{background:rgba(248,81,73,.14);color:var(--red)}
  .exec .meta{color:var(--muted)}
  .exec .live{width:7px;height:7px;border-radius:50%;background:var(--green);animation:pulse 1.4s infinite}
  .blist{margin-bottom:10px}
  .blist h4{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:8px 0 5px}
  .bcard{display:flex;gap:8px;align-items:baseline;padding:5px 10px;border-radius:7px;background:var(--panel);margin-bottom:3px;font-size:12.5px}
  .bcard .bid{color:var(--accent);flex:none;min-width:30px;font-weight:600}
  .bcard .bnm{flex:1;min-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .bcard a{color:inherit;text-decoration:none}
  .bcard a:hover .bnm{color:var(--accent)}
  .bcard .bac{flex:none;font-size:10.5px;color:var(--muted);font-variant-numeric:tabular-nums}
  .bcard .bac.full{color:var(--green)}
  .bcard .bage{flex:none;font-size:10.5px;color:var(--muted)}
  .bcard .blab{flex:none;display:flex;gap:3px}
  .blab span{font-size:9.5px;padding:0 6px;border-radius:999px;border:1px solid var(--border);color:var(--muted)}
  .acts{max-height:220px;overflow-y:auto;font:12px/1.7 Consolas,monospace}
  .act{display:flex;gap:10px;padding:2px 4px;border-bottom:1px solid var(--border)}
  .act:last-child{border-bottom:none}
  .act.done{opacity:.45}
  .act time{color:var(--muted);flex:none;font-variant-numeric:tabular-nums}
  .act code{color:var(--accent);flex:none;width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .act .detail{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#c9d4e0}
</style>
</head>
<body>
<header>
  <h1>Cron Log — Klinik Worker</h1>
  <span class="dot" id="dot"></span>
  <span class="hb" id="hb"></span>
  <div class="spacer"></div>
  <div class="filters" id="filters">
    <button data-f="all" class="on">Semua</button>
    <button data-f="issues">Error / Warning</button>
    <button data-f="results">Kartu Selesai</button>
  </div>
</header>
<main>
  <div id="execwrap" style="padding:10px 18px 0 18px"></div>
  <div id="actwrap" style="padding:0 18px"></div>
  <div id="boardwrap" style="padding:0 18px"></div>
  <div style="display:grid;grid-template-columns:320px 1fr;flex:1;overflow:hidden">
    <aside id="list"></aside>
    <section id="detail"><div class="empty">Pilih run di kiri.</div></section>
  </div>
</main>
<script>
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let DATA=null,FILTER="all",SEL=null,seen=new Set(),first=true;

function renderExec(){
  const host=document.getElementById("execwrap");if(!host)return;
  const x=DATA.execution;
  if(!x||!x.status){host.innerHTML=`<div class="exec"><span class="st n chip" style="background:var(--panel2);color:var(--muted)">TIDAK ADA DATA</span><span class="meta">executions.db tidak terbaca</span></div>`;return;}
  const running=x.status==="running";
  const cls=x.status==="running"?"running":(x.status==="failed"?"failed":"completed");
  let meta=`mulai ${esc(x.started)}`;
  if(running){
    meta+=` · progress ${x.progress_age?esc(x.progress_age)+"s lalu":"baru saja"}`;
    if(x.progress_age&&+x.progress_age>180)meta+=` ⚠`;
  }else{
    meta+=` · selesai ${esc(x.finished||"-")}`;
  }
  host.innerHTML=`<div class="exec ${cls}">
    ${running?'<span class="live"></span>':""}
    <span class="st ${cls}">${esc(x.status.toUpperCase())}</span>
    <span class="meta">${meta}</span>
    ${x.error?`<span class="meta" title="${esc(x.error)}">⚠ ${esc(x.error.slice(0,60))}…</span>`:""}
  </div>`;
  renderActivity();
}

function renderActivity(){
  const host=document.getElementById("actwrap");if(!host||!DATA.activity)return;
  const acts=DATA.activity.slice(-16).reverse();
  if(!acts.length){host.innerHTML=`<div class="block"><h3>Aktivitas Live</h3><div class="empty">Belum ada tool call tercatat.</div></div>`;return;}
  host.innerHTML=`<div class="block"><h3>Aktivitas Live — apa yang sedang dikerjakan worker (terbaru di atas)</h3>
    <div class="acts">${acts.map(a=>{
      const isCall=a.kind==="call";
      const tool=isCall?a.tool:"↳";
      return `<div class="act ${isCall?"":"done"}"><time>${esc(a.time)}</time>
        <code>${esc(tool)}</code>
        <span class="detail">${esc(a.detail||"")}</span></div>`;
    }).join("")}</div></div>`;
}

function renderBoard(){
  const host=document.getElementById("boardwrap");if(!host)return;
  const b=DATA.board;
  if(!b){host.innerHTML="";return;}
  const any=(b.lists||[]).some(l=>l.cards.length);
  if(!any&&!b.error){host.innerHTML="";return;}
  let html=`<div class="block"><h3>Kartu Aktif — semua agent (live dari Trello)</h3>`;
  if(b.error)html+=`<div class="empty" style="text-align:left;padding:4px">Trello: ${esc(b.error)}</div>`;
  for(const ls of (b.lists||[])){
    html+=`<div class="blist"><h4>${esc(ls.name)} — ${ls.cards.length} kartu</h4>`;
    if(!ls.cards.length)html+=`<div class="empty" style="padding:4px;text-align:left">kosong</div>`;
    for(const c of ls.cards.slice(0,25)){
      const parts=(c.ac||"").split("/");
      const full=parts.length===2&&parts[0]===parts[1]&&parts[0]!=="0";
      const age=c.age_min!=null?(c.age_min<60?c.age_min+"m":Math.floor(c.age_min/60)+"j"+(c.age_min%60)+"m"):"";
      const labs=(c.labels||[]).filter(l=>l.name).map(l=>`<span>${esc(l.name)}</span>`).join("");
      html+=`<div class="bcard">
        <span class="bid">#${esc(c.idShort??"?")}</span>
        ${c.url?`<a href="${esc(c.url)}" target="_blank" rel="noopener"><span class="bnm">${esc(c.name)}</span></a>`:`<span class="bnm">${esc(c.name)}</span>`}
        <span class="bac ${full?"full":""}">AC ${esc(c.ac||"-")}</span>
        ${labs?`<span class="blab">${labs}</span>`:""}
        ${age?`<span class="bage">${esc(age)} lalu</span>`:""}
      </div>`;
    }
    html+=`</div>`;
  }
  html+=`</div>`;
  host.innerHTML=html;
}
function classify(r){
  if(r.failure)return"fail";
  if(r.silent)return"silent";
  if(r.warnings.length)return"warn";
  if(r.cards.some(c=>c.to==="review"))return"done";
  return"info";
}
function chips(r){
  const k=classify(r),out=[];
  if(k==="fail")out.push(`<span class="chip r">FAILURE</span>`);
  if(k==="silent")out.push(`<span class="chip n">SILENT</span>`);
  if(r.warnings.length)out.push(`<span class="chip y">${r.warnings.length} warning</span>`);
  const rev=r.cards.filter(c=>c.to==="review").length;
  if(rev)out.push(`<span class="chip g">${rev} kartu → review</span>`);
  return out.join("");
}
function pass(r){
  if(FILTER==="issues")return r.warnings.length>0||r.failure;
  if(FILTER==="results")return r.cards.some(c=>c.to==="review");
  return true;
}
function renderList(){
  const rows=DATA.runs.filter(pass);
  document.getElementById("list").innerHTML=rows.length?rows.map(r=>`
    <div class="run ${r.file===SEL?"sel":""}" data-f="${esc(r.file)}">
      <div class="t"><b>${esc(r.time)}</b><span class="kb">${esc(r.size_kb)} KB</span></div>
      <div class="s">${esc(r.summary||"—")}</div>
      <div class="chips">${chips(r)}</div>
    </div>`).join(""):`<div class="empty">Tidak ada run untuk filter ini.</div>`;
  document.querySelectorAll(".run").forEach(el=>el.onclick=()=>{SEL=el.dataset.f;renderList();renderDetail();});
}
function renderDetail(){
  const r=DATA.runs.find(x=>x.file===SEL);
  const el=document.getElementById("detail");
  if(!r){el.innerHTML=`<div class="empty">Pilih run di kiri.</div>`;return;}
  let html=`<div class="head"><h2>Run ${esc(r.time)}</h2><span class="m">${esc(r.date)} · ${esc(r.size_kb)} KB · ${r.chars.toLocaleString("id-ID")} karakter</span>
    ${r.silent?'<span class="chip n">SILENT</span>':""}${r.failure?'<span class="chip r">FAILURE</span>':""}</div>`;
  if(r.summary)html+=`<div class="block"><h3>Ringkasan</h3><div>${esc(r.summary)}</div></div>`;
  if(r.cards.length)html+=`<div class="block"><h3>Kartu (${r.cards.length}) — progress per kartu</h3><div class="cards">${r.cards.map((c,ci)=>{
    const shas=(c.shas||[]).map(s=>`<a class="sha" href="https://github.com/haidi20/klinik/commit/${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a>`).join("");
    const det=(c.details||[]);
    const detBtn=det.length?`<button class="dtoggle" data-c="${ci}">detail (${det.length}) ▾</button>`:"";
    const detHtml=det.length?`<div class="cdetail" id="cd-${ci}"><ul>${det.map(d=>`<li>${esc(d)}</li>`).join("")}</ul></div>`:"";
    return `<div class="crow"><span class="id">#${esc(c.id)}</span><span class="ttl">${esc(c.title)}</span>
    <span class="to chip ${c.to==="review"?"g":(c.to==="progress"?"y":"n")}">${c.to?"→ "+esc(c.to):"· disebut"}</span>${detBtn}
    <div class="shas">${shas}</div>${detHtml}</div>`;}).join("")}</div></div>`;
  if(r.highlights.length)html+=`<div class="block"><h3>Poin Penting</h3><ul class="hl">${r.highlights.map(h=>`<li>${esc(h)}</li>`).join("")}</ul></div>`;
  if(r.warnings.length)html+=`<div class="block"><h3>Warning / Error</h3><ul class="warn">${r.warnings.map(w=>`<li>${esc(w)}</li>`).join("")}</ul></div>`;
  const cached=RAW_CACHE[r.file];
  html+=`<div class="block"><button id="rawbtn">${RAW_OPEN?"Sembunyikan log mentah ↑":"Tampilkan log mentah lengkap ↓"}</button>
    <div id="raw" class="raw" style="display:${RAW_OPEN?"block":"none"}">${RAW_OPEN?(cached||"memuat…"):""}</div></div>`;
  el.innerHTML=html;
}
let RAW_CACHE={},RAW_OPEN=false,LAST_RENDERED=null;
async function loadRaw(file){
  if(RAW_CACHE[file])return RAW_CACHE[file];
  const r=await fetch("/api/raw?file="+encodeURIComponent(file));
  RAW_CACHE[file]=await r.text();
  return RAW_CACHE[file];
}
document.addEventListener("click",async e=>{
  if(e.target.id==="rawbtn"){
    RAW_OPEN=!RAW_OPEN;
    if(RAW_OPEN&&!RAW_CACHE[SEL]){
      RAW_CACHE[SEL]="memuat…";
      RAW_CACHE[SEL]=await loadRaw(SEL);
    }
    renderDetail();
    const raw=document.getElementById("raw");
    if(raw)raw.scrollTop=0;
  }
  if(e.target.classList&&e.target.classList.contains("dtoggle")){
    const d=document.getElementById("cd-"+e.target.dataset.c);
    if(d){d.classList.toggle("open");
      e.target.textContent=d.classList.contains("open")
        ?e.target.textContent.replace("▾","▴")
        :e.target.textContent.replace("▴","▾");}
  }
});
document.getElementById("filters").onclick=e=>{
  if(e.target.dataset.f){FILTER=e.target.dataset.f;
    document.querySelectorAll(".filters button").forEach(b=>b.classList.toggle("on",b.dataset.f===FILTER));
    renderList();}
};
async function tick(){
  try{
    const r=await fetch("/api/data");DATA=await r.json();
    const j=DATA.job||{};
    document.getElementById("hb").textContent=`heartbeat ${DATA.heartbeat_sec??"-"}s lalu · last run ${j.last_run||"-"} (${j.last_status||"-"}) · next ${j.next_run||"-"}`;
    document.getElementById("dot").classList.toggle("off",!j.enabled);
    renderExec();
    renderBoard();
    if(!SEL&&DATA.runs.length)SEL=DATA.runs[0].file;
    // Render ulang hanya jika pilihan berubah — jangan ganggu raw view yang
    // sedang terbuka saat auto-refresh.
    if(LAST_RENDERED!==SEL){
      renderList();renderDetail();LAST_RENDERED=SEL;
    }else{
      renderList();
    }
  }catch(e){document.getElementById("hb").textContent="koneksi gagal: "+e.message;document.getElementById("dot").classList.add("off");}
}
tick();setInterval(tick,3000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path.startswith("/api/data"):
            body = json.dumps(get_data(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        elif self.path.startswith("/api/raw"):
            # hanya nama file sederhana — cegah path traversal
            from urllib.parse import urlparse, parse_qs, unquote
            q = parse_qs(urlparse(self.path).query)
            name = unquote((q.get("file") or [""])[0])
            safe = Path(name).name
            path = OUTPUT_DIR / safe
            if path.exists() and path.parent == OUTPUT_DIR:
                self._send(200, path.read_bytes(), "text/plain; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")
        else:
            self._send(404, b"not found", "text/plain")


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 8791), Handler)
    print("Cron Log Monitor: http://127.0.0.1:8791")
    srv.serve_forever()


if __name__ == "__main__":
    main()
