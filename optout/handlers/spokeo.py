"""
Spokeo opt-out handler.

Flow:
  1. Go to spokeo.com/opt_out/new
  2. Enter your listing URL (if known) or name + location.
  3. Enter email address.
  4. Submit → email verification required.
"""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.spokeo.com/opt_out/new"


class SpokeoHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        email = p.get("email", "")

        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        # Spokeo's opt-out page asks for the URL of the listing.
        # We open the page so the user can look up their URL and paste it,
        # then fill the email field if we can find it.
        if email:
            await self.try_fill('input[type="email"], input[name*="email" i]', email)

        return await self.pause_for_manual(
            "Spokeo requires the direct URL of your listing. "
            "1) Search spokeo.com for your name and copy the URL of your result. "
            "2) Paste it into the 'Profile URL' field on this opt-out page. "
            "3) Confirm your email and submit. "
            f"Your email ({email}) has been pre-filled if the field was found."
        )
