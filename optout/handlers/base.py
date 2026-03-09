"""Base class for all opt-out handlers."""

import asyncio
from playwright.async_api import Page


class BaseHandler:
    """
    Subclass this for each platform. Implement `run()`.

    Statuses returned by run():
      submitted          – form submitted successfully (may still need email confirmation)
      email_required     – submitted; user must click a confirmation email to finalize
      phone_required     – submitted; user must verify via SMS/phone call
      captcha_required   – hit a CAPTCHA; user must complete it manually
      manual_required    – could not automate; browser left open for user to complete
      already_done       – this broker was previously completed (from results log)
      skipped            – broker skipped (e.g. --only filter didn't match)
      failed             – unrecoverable error
    """

    def __init__(self, broker: dict, config: dict, page: Page):
        self.broker = broker
        self.config = config
        self.page = page
        self.p = config["personal"]

    async def run(self) -> dict:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def goto(self, url: str | None = None):
        target = url or self.broker["opt_out_url"]
        await self.page.goto(target, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(1.5)

    async def pause_for_manual(self, message: str) -> dict:
        """Print instructions and wait for the user to press Enter."""
        name = self.broker["name"]
        print(f"\n  [!] Manual step needed for {name}:")
        print(f"      {message}")
        print(f"      Browser is open at: {self.page.url}")
        input("      Press Enter when finished > ").strip()
        return {"status": "manual_required", "notes": message}

    async def try_fill(self, selector: str, value: str, timeout: int = 3000) -> bool:
        """Fill a field if it exists; return True on success."""
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception:
            return False

    async def try_click(self, selector: str, timeout: int = 5000) -> bool:
        """Click an element if it exists; return True on success."""
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def wait_for_any(self, selectors: list[str], timeout: int = 8000) -> str | None:
        """Return the first selector that becomes visible within timeout."""
        tasks = []
        for sel in selectors:
            tasks.append(
                self.page.wait_for_selector(sel, state="visible", timeout=timeout)
            )
        done, _ = await asyncio.wait(
            [asyncio.create_task(t) for t in tasks],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout / 1000,
        )
        if done:
            return True
        return None

    def _first(self, *keys: str) -> str:
        """Return first non-empty value from personal config keys."""
        for k in keys:
            v = self.p.get(k, "")
            if v:
                return str(v)
        return ""
