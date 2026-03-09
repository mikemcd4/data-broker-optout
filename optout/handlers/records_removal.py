"""
Handler for the shared records-removal platform (/ng/control/privacy).
Pre-fills the form, then pauses for CAPTCHA solve + submit.
"""

import asyncio
from .base import BaseHandler


class RecordsRemovalHandler(BaseHandler):

    async def run(self) -> dict:
        email = self.p.get("email", "")

        try:
            await self.goto()
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await self.fill_form()

        if await self.has_captcha():
            solved = await self.solve_captcha()
            if not solved:
                print(f"      [CAPTCHA] Please solve the CAPTCHA, then press Enter.")
                input("      Press Enter after solving > ")

        submitted = await self.submit_form()
        if submitted:
            return {
                "status": "email_required",
                "notes": f"Submitted. Check {email} for a confirmation link.",
            }

        return await self.pause_for_manual(
            "Form pre-filled. Please click Submit to complete."
        )
