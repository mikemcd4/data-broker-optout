"""
BeenVerified platform handler.

Sites using this platform:
  beenverified.com, freephonetracer.com, and others that redirect to
  beenverified.com/app/optout/search

Flow:
  1. Go to search page.
  2. Fill first name, last name, state.
  3. Click Search.
  4. Wait for results; find the matching record.
  5. Click "Opt-Out This Listing".
  6. Enter email.
  7. Submit → email verification required.
"""

import asyncio
from .base import BaseHandler

OPTOUT_SEARCH_URL = "https://www.beenverified.com/app/optout/search"


class BeenVerifiedHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        state = p.get("address", {}).get("state", "")
        email = p.get("email", "")

        if not first or not last:
            return {"status": "failed", "notes": "first_name and last_name required."}

        try:
            await self.goto(OPTOUT_SEARCH_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        # Fill the search form — BeenVerified uses React; fields may take a moment
        await asyncio.sleep(1)
        filled = 0
        for sel in ['input[name="firstName"]', 'input[placeholder*="First" i]', 'input[id*="first" i]']:
            if await self.try_fill(sel, first, timeout=3000):
                filled += 1
                break
        for sel in ['input[name="lastName"]', 'input[placeholder*="Last" i]', 'input[id*="last" i]']:
            if await self.try_fill(sel, last, timeout=3000):
                filled += 1
                break

        # State dropdown
        if state:
            try:
                await self.page.select_option('select[name="state"], select[id*="state" i]', state, timeout=3000)
            except Exception:
                await self.try_fill('input[name="state"], input[placeholder*="State" i]', state)

        # Submit search — BeenVerified uses a styled button, try multiple selectors
        clicked = False
        for sel in [
            'button[type="submit"]',
            'button:has-text("Search")',
            'input[type="submit"]',
            '[data-testid*="search"]',
            'button.btn-primary',
        ]:
            if await self.try_click(sel, timeout=3000):
                clicked = True
                break

        if not clicked or filled < 2:
            return await self.pause_for_manual(
                "Please fill in your name and state, then click Search, "
                "find your listing, and click Opt-Out."
            )

        await asyncio.sleep(4)

        # Try to find an opt-out button in the results
        optout_btn = self.page.locator(
            'a:has-text("Opt-Out"), button:has-text("Opt-Out"), '
            'a:has-text("Opt Out This Listing"), button:has-text("Opt Out This Listing")'
        ).first
        try:
            if await optout_btn.is_visible(timeout=8000):
                await optout_btn.click()
                await asyncio.sleep(2)
            else:
                return await self.pause_for_manual(
                    "Search complete. Please find your listing and click Opt-Out manually."
                )
        except Exception:
            return await self.pause_for_manual(
                "Search complete. Please find your listing and click Opt-Out manually."
            )

        # Enter email for confirmation
        if email:
            await self.try_fill('input[type="email"], input[name*="email" i]', email)

        submitted = await self.try_click(
            'button[type="submit"], button:has-text("Submit"), button:has-text("Send")'
        )
        if submitted:
            return {
                "status": "email_required",
                "notes": f"Opt-out submitted. Check {email} for a confirmation link.",
            }

        return await self.pause_for_manual(
            "Almost done — please enter your email and submit the opt-out form."
        )
