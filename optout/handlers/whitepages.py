"""
Whitepages suppression-request handler.

Flow:
  1. Go to whitepages.com/suppression-requests
  2. The page will redirect to a search; fill in name + location.
  3. Find the record and click Remove.
  4. Requires phone (SMS) verification — pause for manual completion.
"""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.whitepages.com/suppression-requests"


class WhitepagesHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        addr = p.get("address", {})
        city = addr.get("city", "")
        state = addr.get("state", "")

        if not first or not last:
            return {"status": "failed", "notes": "first_name and last_name required."}

        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        # Whitepages has an "Edit my listing" search on the suppression page
        await self.try_fill('input[name*="name" i], input[placeholder*="name" i]', f"{first} {last}")
        if city and state:
            await self.try_fill(
                'input[name*="location" i], input[placeholder*="city" i]',
                f"{city}, {state}",
            )

        await self.try_click('button[type="submit"], button:has-text("Search")', timeout=4000)
        await asyncio.sleep(3)

        # Phone verification is always required on Whitepages — hand off to user
        return await self.pause_for_manual(
            "Whitepages requires SMS phone verification. "
            "Please find your listing, click 'Remove me', and complete the phone verification."
        )
