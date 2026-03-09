"""
Intelius platform handler.

Sites using this platform:
  intelius.com, addresses.com, infospace.com, irbsearch.com, and others
  that redirect to intelius.com/opt-out/submit/

Flow:
  1. Navigate to https://www.intelius.com/opt-out/submit/
  2. Fill first name, last name, city, state.
  3. Click Search.
  4. Select matching record and continue.
  5. Enter email → email verification required.
"""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.intelius.com/opt-out/submit/"


class InteliusHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        addr = p.get("address", {})
        city = addr.get("city", "")
        state = addr.get("state", "")
        email = p.get("email", "")

        if not first or not last:
            return {"status": "failed", "notes": "first_name and last_name required."}

        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        await self.try_fill('input[name="firstName"], input[placeholder*="First" i]', first)
        await self.try_fill('input[name="lastName"], input[placeholder*="Last" i]', last)
        if city:
            await self.try_fill('input[name="city"], input[placeholder*="City" i]', city)
        if state:
            try:
                await self.page.select_option('select[name="state"]', state)
            except Exception:
                await self.try_fill('input[name="state"]', state)

        clicked = await self.try_click(
            'button[type="submit"], button:has-text("Search"), input[value*="Search" i]'
        )
        if not clicked:
            return await self.pause_for_manual(
                "Could not click Search. Please search and opt-out manually."
            )

        await asyncio.sleep(4)

        # Try to click the first opt-out / select button
        optout = self.page.locator(
            'button:has-text("Opt Out"), a:has-text("Opt Out"), '
            'button:has-text("Remove"), input[value*="Opt Out" i]'
        ).first
        try:
            if await optout.is_visible(timeout=8000):
                await optout.click()
                await asyncio.sleep(2)
            else:
                return await self.pause_for_manual(
                    "Search done. Please select your record and click Opt Out manually."
                )
        except Exception:
            return await self.pause_for_manual(
                "Search done. Please select your record and click Opt Out manually."
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
