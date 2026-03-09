"""PeopleFinders opt-out handler."""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.peoplefinders.com/opt-out"


class PeopleFinderHandler(BaseHandler):

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
            'button:has-text("Opt Out"), a:has-text("Opt Out"), button:has-text("Remove")'
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
            "Search submitted. Find your record, click Opt Out, and confirm your email."
        )
