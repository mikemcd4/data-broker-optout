"""
Whitepages suppression-request handler.

Requires phone (SMS) verification — cannot be fully automated.
We navigate to the page and pause for the user to complete it.
"""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.whitepages.com/suppression-requests"


class WhitepagesHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last = p.get("last_name", "")

        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        return await self.pause_for_manual(
            f"Search for '{first} {last}', find your listing, "
            f"click 'Remove me', and complete the SMS verification."
        )
