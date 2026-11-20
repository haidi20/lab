from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from modules.inaproc.api.auth import AuthError
from modules.inaproc.api.cache import TkdnMysqlStore
from modules.inaproc.api.collector import Collector
from modules.inaproc.api.config import GatewayConfig, InaprocDbConfig, load_env_file
from modules.inaproc.api.db import connect_mysql
from modules.inaproc.api.exporter import to_csv, to_json
from modules.inaproc.api.gateway_sync import SCOPES
from modules.inaproc.api.login import login_interaktif
from modules.inaproc.api.scraper import TkdnScraper
from modules.inaproc.api.spt import SptNumber

DEFAULT_SESSION = Path("modules/inaproc/storageState.json")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m modules.inaproc")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_session_options(target):
        target.add_argument(
            "--session",
            default=str(DEFAULT_SESSION),
            help="Path to the INAPROC storageState.json file",
        )

    login = sub.add_parser("login", help="Interactive INAPROC login for OTP/captcha")
    add_session_options(login)

    probe = sub.add_parser("probe", help="Open one SPT number and report parsed rows")
    add_session_options(probe)
    probe.add_argument("--nomor", required=True, dest="nomor")
    probe.add_argument("--json", action="store_true", dest="as_json")

    collect = sub.add_parser("collect", help="Collect a sequence range into MySQL")
    add_session_options(collect)
    collect.add_argument("--nomor", required=True, dest="nomor")
    collect.add_argument("--start", type=int, required=True)
    collect.add_argument("--end", type=int, required=True)
    collect.add_argument("--out", default=None)
    collect.add_argument("--delay-min", type=float, default=1.0)
    collect.add_argument("--delay-max", type=float, default=3.0)
    collect.add_argument("--force", action="store_true")

    sub.add_parser("gateway-status", help="Show safe INAPROC Gateway status")
    return parser

def _store() -> TkdnMysqlStore:
    config = InaprocDbConfig.from_env()
    store = TkdnMysqlStore(lambda: connect_mysql(config))
    store.create_schema()
    return store

def _cmd_login(args) -> int:
    result = login_interaktif(args.session)
    print(f"INAPROC session connected: {result['session_path']}")
    return 0

def _cmd_probe(args) -> int:
    scraper = TkdnScraper(args.session)
    result = scraper.fetch(SptNumber.parse(args.nomor))
    payload = {
        "number": args.nomor,
        "status": result.status,
        "row_count": len(result.rows),
        "rows": result.rows,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{args.nomor}: {result.status} ({len(result.rows)} rows)")
        for row in result.rows:
            print(
                f"- {row.get('product_type')} | {row.get('brand')} | "
                f"{row.get('type')} | {row.get('value')}"
            )
    return 0

def _cmd_collect(args) -> int:
    store = _store()
    collector = Collector(
        store,
        TkdnScraper(args.session),
        delay_min=args.delay_min,
        delay_max=args.delay_max,
    )
    job = collector.collect(SptNumber.parse(args.nomor), args.start, args.end)
    print(json.dumps(job.as_dict(), ensure_ascii=False, indent=2))
    if args.out:
        rows = store.search(page=1, per_page=100_000)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(to_csv(rows), encoding="utf-8")
        out.with_suffix(".json").write_text(to_json(rows), encoding="utf-8")
        print(f"exported {len(rows)} rows to {out} and {out.with_suffix('.json')}")
    return 0

def _cmd_gateway_status(_args) -> int:
    config = GatewayConfig.from_env()
    state = "enabled" if config.enabled else "disabled"
    print(f"INAPROC Gateway: {state}")
    print(f"base_url: {config.base_url}")
    print(f"token_present: {'yes' if config.token else 'no'}")
    print("scopes: " + ", ".join(SCOPES))
    return 0

def main(argv: Sequence[str] | None = None) -> int:
    load_env_file()
    args = build_parser().parse_args(argv)
    handlers = {
        "login": _cmd_login,
        "probe": _cmd_probe,
        "collect": _cmd_collect,
        "gateway-status": _cmd_gateway_status,
    }
    try:
        return handlers[args.command](args)
    except (AuthError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
