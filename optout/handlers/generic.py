"""
Generic handler for brokers that don't have a dedicated handler.

Strategy:
1. Navigate to the opt-out URL.
2. Try common selector patterns to fill name/email/state fields.
3. Submit if we filled at least name+email.
4. Fall back to manual if the page doesn't match any known pattern.
"""

import asyncio
from .base import BaseHandler

# Common CSS/text selectors for typical opt-out forms
FIRST_NAME_SELECTORS = [
    'input[name*="first" i]',
    'input[id*="first" i]',
    'input[placeholder*="first name" i]',
    'input[aria-label*="first name" i]',
]
LAST_NAME_SELECTORS = [
    'input[name*="last" i]',
    'input[id*="last" i]',
    'input[placeholder*="last name" i]',
    'input[aria-label*="last name" i]',
]
EMAIL_SELECTORS = [
    'input[type="email"]',
    'input[name*="email" i]',
    'input[id*="email" i]',
    'input[placeholder*="email" i]',
]
STATE_SELECTORS = [
    'select[name*="state" i]',
    'select[id*="state" i]',
    'input[name*="state" i]',
    'input[id*="state" i]',
    'input[placeholder*="state" i]',
]
SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit")',
    'button:has-text("Opt Out")',
    'button:has-text("Opt-Out")',
    'button:has-text("Remove")',
    'button:has-text("Send Request")',
    'button:has-text("Request Removal")',
    'button:has-text("Continue")',
    'a:has-text("Opt Out")',
    'a:has-text("Remove Me")',
]
SUCCESS_PATTERNS = [
    "successfully",
    "thank you",
    "request received",
    "opted out",
    "removal request",
    "been submitted",
    "confirmation",
    "verify your email",
]


async def _try_selectors(page, selectors, value):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=1500):
                await loc.fill(value)
                return True
        except Exception:
            continue
    return False


class GenericHandler(BaseHandler):

    async def run(self) -> dict:
        try:
            await self.goto()
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        # Some pages need a moment to hydrate
        await asyncio.sleep(2)

        filled = 0
        first = self.p.get("first_name", "")
        last = self.p.get("last_name", "")
        email = self.p.get("email", "")
        state = self.p.get("address", {}).get("state", "")

        if first and await _try_selectors(self.page, FIRST_NAME_SELECTORS, first):
            filled += 1
        if last and await _try_selectors(self.page, LAST_NAME_SELECTORS, last):
            filled += 1
        if email and await _try_selectors(self.page, EMAIL_SELECTORS, email):
            filled += 1
        if state:
            await _try_selectors(self.page, STATE_SELECTORS, state)

        if filled < 2:
            # Couldn't reliably fill the form — leave it open for the user
            return await self.pause_for_manual(
                "Could not auto-fill the opt-out form. Please complete it manually."
            )

        # Try to submit
        submitted = False
        for sel in SUBMIT_SELECTORS:
            try:
                btn = self.page.locator(sel).first
                if await btn.is_visible(timeout=1500):
                    await btn.click()
                    submitted = True
                    break
            except Exception:
                continue

        if not submitted:
            return await self.pause_for_manual(
                "Form filled but could not find a submit button. Please submit manually."
            )

        await asyncio.sleep(3)

        # Check for success text
        page_text = (await self.page.content()).lower()
        success = any(p in page_text for p in SUCCESS_PATTERNS)

        needs_email = self.broker.get("needs_email_verification", False)
        needs_email = needs_email or "verify" in page_text or "confirm" in page_text

        if success or submitted:
            if needs_email:
                return {
                    "status": "email_required",
                    "notes": f"Submitted. Check {email} for a confirmation link.",
                }
            return {"status": "submitted", "notes": "Form submitted successfully."}

        return await self.pause_for_manual(
            "Form submitted but could not confirm success. Please verify manually."
        )
