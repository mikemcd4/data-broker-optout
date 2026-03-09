"""InstantCheckmate opt-out handler."""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.instantcheckmate.com/opt-out/"


class InstantCheckmateHandler(BaseHandler):

    async def run(self) -> dict:
        email = self.p.get("email", "")

        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await self.fill_form()
        await self.submit_form()
        await asyncio.sleep(4)

        optout = self.page.locator(
            'button:has-text("Opt Out"), a:has-text("Opt Out"), '
            'button:has-text("Opt-Out This Listing")'
        ).first
        try:
            if await optout.is_visible(timeout=8000):
                await optout.click()
                await asyncio.sleep(2)
                await self.fill_form()
                await self.submit_form()
                return {
                    "status": "email_required",
                    "notes": f"Submitted. Check {email} for a confirmation email.",
                }
        except Exception:
            pass

        return await self.pause_for_manual(
            "Search submitted. Find your listing, click Opt Out, and confirm your email."
        )
