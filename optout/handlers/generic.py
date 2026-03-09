"""
Generic handler — uses JS label-matching to fill any form automatically.

Flow:
1. Navigate to opt-out URL.
2. Inject JS to fill all visible fields by label text.
3. If CAPTCHA found, pause for user to solve it then auto-submit after.
4. Auto-submit.
5. Check result page for success/email-verification language.
6. Only pause for manual if we filled nothing at all.
"""

import asyncio
from .base import BaseHandler

SUCCESS_PATTERNS = [
    "successfully", "thank you", "request received", "opted out",
    "removal request", "been submitted", "we'll process", "has been submitted",
]
EMAIL_PATTERNS = [
    "verify your email", "confirmation email", "check your email",
    "click the link", "sent you an email",
]


class GenericHandler(BaseHandler):

    async def run(self) -> dict:
        try:
            await self.goto()
        except Exception as e:
            return {"status": "failed", "notes": f"Navigation error: {e}"}

        filled = await self.fill_form()

        if filled == 0:
            # Nothing matched — leave page open for user
            return await self.pause_for_manual(
                "Could not detect form fields. Please fill in and submit manually."
            )

        # If CAPTCHA present, let user solve it — we'll submit after
        if await self.has_captcha():
            print(f"      [CAPTCHA] Please solve the CAPTCHA, then press Enter.")
            input("      Press Enter after solving CAPTCHA > ")

        submitted = await self.submit_form()

        if not submitted:
            # Form filled but no submit button found — let user click it
            return await self.pause_for_manual(
                f"Filled {filled} field(s) but could not find submit button. Please click it."
            )

        page_text = (await self.page.content()).lower()

        if any(p in page_text for p in EMAIL_PATTERNS) or self.broker.get("needs_email_verification"):
            return {
                "status": "email_required",
                "notes": f"Submitted. Check {self.p.get('email','')} for a confirmation link.",
            }

        if any(p in page_text for p in SUCCESS_PATTERNS) or submitted:
            return {"status": "submitted", "notes": f"Auto-submitted ({filled} fields filled)."}

        return await self.pause_for_manual(
            "Submitted but could not confirm success. Please verify."
        )
