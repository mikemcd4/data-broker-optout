"""
BeenVerified platform handler.
Search for your record, click Opt-Out, confirm via email.
"""

import asyncio
from .base import BaseHandler

OPTOUT_SEARCH_URL = "https://www.beenverified.com/app/optout/search"


class BeenVerifiedHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last  = p.get("last_name", "")
        email = p.get("email", "")

        try:
            await self.goto(OPTOUT_SEARCH_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        filled = await self.fill_form()

        if filled == 0:
            return await self.pause_for_manual(
                f"Enter your name ({first} {last}) and state, click Search, "
                "find your listing, and click Opt-Out."
            )

        await self.submit_form()
        await asyncio.sleep(4)

        # Try to click opt-out on results page
        optout = self.page.locator(
            'a:has-text("Opt-Out"), button:has-text("Opt-Out"), '
            'a:has-text("Opt Out This Listing"), button:has-text("Opt Out This Listing")'
        ).first
        try:
            if await optout.is_visible(timeout=8000):
                await optout.click()
                await asyncio.sleep(2)
                await self.fill_form()
                await self.submit_form()
                return {
                    "status": "email_required",
                    "notes": f"Opt-out submitted. Check {email} for a confirmation link.",
                }
        except Exception:
            pass

        return await self.pause_for_manual(
            "Search submitted. Find your listing, click Opt-Out, and enter your email."
        )
