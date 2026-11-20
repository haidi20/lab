from __future__ import annotations

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:5174/")
    parser.add_argument("--out", default="modules/inaproc/documents/smoke")
    parser.add_argument("--channel", default="chrome")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        launch_args = {"channel": args.channel} if args.channel else {}
        if os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"):
            launch_args["executable_path"] = os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]
        browser = playwright.chromium.launch(**launch_args)
        for name, viewport in (
            ("desktop", {"width": 1440, "height": 1100}),
            ("mobile", {"width": 390, "height": 900}),
        ):
            page = browser.new_page(viewport=viewport)
            errors: list[str] = []
            page.on(
                "console",
                lambda message: errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.goto(args.base_url, wait_until="networkidle")
            page.wait_for_timeout(1200)
            overflow = page.evaluate(
                "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            print(
                name,
                "overflow=", overflow,
                "h1=", page.locator("h1").inner_text(),
                "panels=", page.locator("section.panel").count(),
                "rows=", page.locator("table tbody tr").count(),
                "errors=", errors,
            )
            page.screenshot(path=str(out / f"{name}.png"), full_page=True)
            page.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
