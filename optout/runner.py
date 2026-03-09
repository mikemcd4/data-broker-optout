"""
Main runner: loads brokers + config, spins up Playwright, iterates through brokers.
"""

import asyncio
import os
import sys
from colorama import Fore, Style, init as colorama_init

from playwright.async_api import async_playwright

from .logger import ResultsLog
from .handlers.factory import get_handler

colorama_init(autoreset=True)

STATUS_COLOR = {
    "submitted": Fore.GREEN,
    "email_required": Fore.CYAN,
    "phone_required": Fore.CYAN,
    "captcha_required": Fore.YELLOW,
    "manual_required": Fore.YELLOW,
    "already_done": Fore.BLUE,
    "skipped": Fore.WHITE,
    "failed": Fore.RED,
}

STATUS_ICON = {
    "submitted": "+",
    "email_required": "@",
    "phone_required": "#",
    "captcha_required": "!",
    "manual_required": "!",
    "already_done": "-",
    "skipped": ".",
    "failed": "x",
}


def _print_status(broker_name: str, status: str, notes: str = ""):
    color = STATUS_COLOR.get(status, Fore.WHITE)
    icon = STATUS_ICON.get(status, "?")
    label = status.replace("_", " ").upper()
    print(f"  {color}{icon} [{label}]{Style.RESET_ALL} {broker_name}")
    if notes:
        print(f"      {Fore.WHITE}{notes}{Style.RESET_ALL}")


async def run(
    brokers: list[dict],
    config: dict,
    log: ResultsLog,
    *,
    only: str | None = None,
    resume: bool = False,
    headless: bool = False,
    delay: float = 1.0,
):
    total = len(brokers)
    done_count = 0
    fail_count = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        for i, broker in enumerate(brokers, 1):
            broker_id = broker["id"]
            name = broker["name"]

            # Filter by --only
            if only and only.lower() not in name.lower() and only.lower() != broker_id:
                continue

            # Skip already-completed if --resume
            if resume and log.is_done(broker_id):
                _print_status(name, "already_done")
                done_count += 1
                continue

            print(f"\n[{i}/{total}] {Style.BRIGHT}{name}{Style.RESET_ALL}")
            print(f"  URL: {broker['opt_out_url']}")

            handler = get_handler(broker, config, page)

            try:
                result = await asyncio.wait_for(handler.run(), timeout=120)
            except asyncio.TimeoutError:
                result = {"status": "failed", "notes": "Timed out after 120 s."}
            except Exception as exc:
                result = {"status": "failed", "notes": str(exc)}

            status = result.get("status", "failed")
            notes = result.get("notes", "")
            log.record(broker_id, status, notes)
            _print_status(name, status, notes)

            if status in ("submitted", "email_required", "phone_required"):
                done_count += 1
            elif status == "failed":
                fail_count += 1

            await asyncio.sleep(delay)

        await browser.close()

    print(f"\n{Style.BRIGHT}-- Summary --------------------------------------{Style.RESET_ALL}")
    for status, count in log.summary().items():
        color = STATUS_COLOR.get(status, Fore.WHITE)
        print(f"  {color}{STATUS_ICON.get(status, '?')} {status}: {count}{Style.RESET_ALL}")
    print(f"\n  Results saved to: {os.path.abspath(log.path)}")
