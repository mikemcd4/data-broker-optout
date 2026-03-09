"""
Handler for the 'records removal' platform.

Sites using this shared platform have opt-out URLs ending in:
  /ng/control/privacy  or  /ex/control/privacy

Examples: backgroundcheck.run, centeda.com, councilon.com, dataveria.com,
          newenglandfacts.com, people-background-check.com

Flow:
  1. Navigate to the opt-out URL.
  2. Fill the privacy-removal form (typically: first name, last name, state, email).
  3. There is usually a CAPTCHA — pause for user to solve it.
  4. Submit.
"""

import asyncio
from .base import BaseHandler


class RecordsRemovalHandler(BaseHandler):

    async def run(self) -> dict:
        p = self.p
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        state = p.get("address", {}).get("state", "")
        email = p.get("email", "")

        try:
            await self.goto()
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        await asyncio.sleep(2)

        # These platforms use a fairly standard form
        for sel in ['input[name*="firstName" i]', 'input[placeholder*="First" i]', 'input[name*="fname" i]']:
            if await self.try_fill(sel, first, timeout=2000):
                break
        for sel in ['input[name*="lastName" i]', 'input[placeholder*="Last" i]', 'input[name*="lname" i]']:
            if await self.try_fill(sel, last, timeout=2000):
                break
        if state:
            try:
                await self.page.select_option('select[name*="state" i]', state, timeout=2000)
            except Exception:
                await self.try_fill('input[name*="state" i], input[placeholder*="State" i]', state)
        if email:
            for sel in ['input[type="email"]', 'input[name*="email" i]', 'input[placeholder*="email" i]']:
                if await self.try_fill(sel, email, timeout=2000):
                    break

        # Always pause for CAPTCHA — these sites virtually always have one
        return await self.pause_for_manual(
            "Form pre-filled. Please solve the CAPTCHA (if present) and click Submit."
        )

        # (unreachable — kept for reference if CAPTCHA detection is added back)
        submitted = await self.try_click(
            'button[type="submit"], input[type="submit"], '
            'button:has-text("Submit"), button:has-text("Send Request")',
            timeout=4000,
        )
        if submitted:
            await asyncio.sleep(3)
            needs_email = self.broker.get("needs_email_verification", False)
            page_text = (await self.page.content()).lower()
            needs_email = needs_email or "verify" in page_text or "confirm your email" in page_text
            if needs_email:
                return {
                    "status": "email_required",
                    "notes": f"Submitted. Check {email} for a confirmation link.",
                }
            return {"status": "submitted", "notes": "Opt-out request submitted."}

        return await self.pause_for_manual(
            "Form filled but could not submit automatically. Please click Submit."
        )
