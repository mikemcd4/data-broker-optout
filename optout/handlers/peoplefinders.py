"""
PeopleFinders opt-out handler.

Flow:
  1. Go to peoplefinders.com/opt-out
  2. Fill name and state.
  3. Find record, click Opt Out.
  4. Enter email → email verification required.
"""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.peoplefinders.com/opt-out"


class PeopleFinderHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        state = p.get("address", {}).get("state", "")
        email = p.get("email", "")

        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        await self.try_fill('input[name*="first" i], input[placeholder*="First" i]', first)
        await self.try_fill('input[name*="last" i], input[placeholder*="Last" i]', last)
        if state:
            try:
                await self.page.select_option('select[name*="state" i]', state)
            except Exception:
                await self.try_fill('input[name*="state" i]', state)

        await self.try_click(
            'button[type="submit"], button:has-text("Search"), input[value*="Search" i]'
        )
        await asyncio.sleep(4)

        optout = self.page.locator(
            'button:has-text("Opt Out"), a:has-text("Opt Out"), '
            'button:has-text("Remove"), a:has-text("Remove")'
        ).first
        try:
            if await optout.is_visible(timeout=8000):
                await optout.click()
                await asyncio.sleep(2)
            else:
                return await self.pause_for_manual(
                    "Search done. Please locate your record and click Opt Out."
                )
        except Exception:
            return await self.pause_for_manual(
                "Search done. Please locate your record and click Opt Out."
            )

        if email:
            await self.try_fill('input[type="email"], input[name*="email" i]', email)

        submitted = await self.try_click(
            'button[type="submit"], button:has-text("Submit"), button:has-text("Continue")'
        )
        if submitted:
            return {
                "status": "email_required",
                "notes": f"Submitted. Check {email} for a confirmation email.",
            }

        return await self.pause_for_manual(
            "Please enter your email and submit the opt-out form."
        )
