"""Spokeo opt-out handler. Requires the listing URL — always manual."""

import asyncio
from .base import BaseHandler

OPTOUT_URL = "https://www.spokeo.com/opt_out/new"


class SpokeoHandler(BaseHandler):

    async def run(self) -> dict:
        try:
            await self.goto(OPTOUT_URL)
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await self.fill_form()

        return await self.pause_for_manual(
            "Spokeo needs the URL of your listing. "
            "Search spokeo.com for your name, copy the result URL, "
            "paste it in the 'Profile URL' field, and submit."
        )
