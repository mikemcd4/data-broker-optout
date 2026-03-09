"""Base class for all opt-out handlers."""

import asyncio
from playwright.async_api import Page
from optout.captcha import detect_and_solve


# JS injected into pages to fill form fields by label text.
# Works with React, Vue, and plain HTML (triggers synthetic events).
_FILL_SCRIPT = """
(userData) => {
    function setNativeValue(el, value) {
        const proto = Object.getPrototypeOf(el);
        const setter = Object.getOwnPropertyDescriptor(proto, 'value');
        if (setter && setter.set) {
            setter.set.call(el, value);
        } else {
            el.value = value;
        }
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function getLabelText(el) {
        // 1. <label for="id">
        if (el.id) {
            const lbl = document.querySelector('label[for="' + el.id + '"]');
            if (lbl) return lbl.innerText.toLowerCase();
        }
        // 2. parent <label>
        const parentLbl = el.closest('label');
        if (parentLbl) return parentLbl.innerText.toLowerCase();
        // 3. aria-label
        if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').toLowerCase();
        // 4. placeholder / name / id
        return ((el.placeholder || '') + ' ' + (el.name || '') + ' ' + (el.id || '')).toLowerCase();
    }

    function selectState(el, state) {
        const opts = [...el.options];
        const match = opts.find(o =>
            o.value.toUpperCase() === state.toUpperCase() ||
            o.text.toUpperCase()  === state.toUpperCase() ||
            o.text.toUpperCase().startsWith(state.toUpperCase())
        );
        if (match) {
            el.value = match.value;
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        }
        return false;
    }

    let filled = 0;
    const inputs = [...document.querySelectorAll(
        'input:not([type=hidden]):not([type=submit]):not([type=button])' +
        ':not([type=checkbox]):not([type=radio]):not([type=file]), select, textarea'
    )].filter(el => {
        const s = window.getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetHeight > 0;
    });

    for (const el of inputs) {
        const lbl = getLabelText(el);

        if (/first.?name|fname|given/i.test(lbl)) {
            setNativeValue(el, userData.firstName); filled++;
        } else if (/last.?name|lname|surname|family/i.test(lbl)) {
            setNativeValue(el, userData.lastName); filled++;
        } else if (/full.?name|your.?name/i.test(lbl) && !userData._fullNameDone) {
            setNativeValue(el, userData.firstName + ' ' + userData.lastName);
            userData._fullNameDone = true; filled++;
        } else if (/e.?mail/i.test(lbl)) {
            setNativeValue(el, userData.email); filled++;
        } else if (/phone|mobile|cell/i.test(lbl)) {
            setNativeValue(el, userData.phone); filled++;
        } else if (/zip|postal/i.test(lbl)) {
            setNativeValue(el, userData.zip); filled++;
        } else if (/city|town/i.test(lbl)) {
            setNativeValue(el, userData.city); filled++;
        } else if (/state|province/i.test(lbl)) {
            if (el.tagName === 'SELECT') {
                if (selectState(el, userData.state)) filled++;
            } else {
                setNativeValue(el, userData.state); filled++;
            }
        } else if (/age|birth.?year|year.?born/i.test(lbl)) {
            setNativeValue(el, userData.birthYear); filled++;
        }
    }
    return filled;
}
"""

_SUBMIT_SCRIPT = """
() => {
    const candidates = [...document.querySelectorAll(
        'button[type=submit], input[type=submit], ' +
        'button:not([type]), [role=button]'
    )].filter(el => {
        const s = window.getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetHeight > 0;
    });

    const keywords = /submit|opt.?out|remove|send|continue|request|search/i;
    const btn = candidates.find(el => keywords.test(el.innerText || el.value || ''))
             || candidates[0];
    if (btn) { btn.click(); return btn.innerText || btn.value || 'clicked'; }
    return null;
}
"""


class BaseHandler:
    """
    Statuses returned by run():
      submitted          - form submitted, no further action needed
      email_required     - submitted; user must click a confirmation email
      phone_required     - submitted; user must verify via SMS
      manual_required    - could not automate; browser left open for user
      already_done       - previously completed
      failed             - unrecoverable error
    """

    def __init__(self, broker: dict, config: dict, page: Page):
        self.broker = broker
        self.config = config
        self.page = page
        self.p = config["personal"]

    async def run(self) -> dict:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    async def goto(self, url: str | None = None):
        target = url or self.broker["opt_out_url"]
        await self.page.goto(target, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(2)

    async def fill_form(self) -> int:
        """
        Inject JS to fill all visible form fields by label text.
        Returns the number of fields successfully filled.
        """
        p = self.p
        addr = p.get("address", {})
        user_data = {
            "firstName": p.get("first_name", ""),
            "lastName":  p.get("last_name", ""),
            "email":     p.get("email", ""),
            "phone":     p.get("phone", ""),
            "city":      addr.get("city", ""),
            "state":     addr.get("state", ""),
            "zip":       addr.get("zip", ""),
            "birthYear": str(p.get("birth_year", "")),
        }
        try:
            filled = await self.page.evaluate(_FILL_SCRIPT, user_data)
            return filled or 0
        except Exception:
            return 0

    async def submit_form(self) -> bool:
        """Click the most likely submit button. Returns True if a button was clicked."""
        try:
            result = await self.page.evaluate(_SUBMIT_SCRIPT)
            if result:
                await asyncio.sleep(3)
                return True
        except Exception:
            pass
        return False

    async def has_captcha(self) -> bool:
        try:
            count = await self.page.locator(
                'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], '
                '.g-recaptcha, .h-captcha, iframe[title*="challenge"]'
            ).count()
            return count > 0
        except Exception:
            return False

    async def solve_captcha(self) -> bool:
        """Attempt to auto-solve CAPTCHA if an API key is configured."""
        api_key = self.config.get("captcha_api_key", "")
        if not api_key:
            return False
        return await detect_and_solve(self.page, api_key)

    async def pause_for_manual(self, message: str) -> dict:
        name = self.broker["name"]
        print(f"\n  [!] Manual step needed for {name}:")
        print(f"      {message}")
        print(f"      URL: {self.page.url}")
        input("      Done? Press Enter to continue > ")
        return {"status": "manual_required", "notes": message}

    async def try_click(self, selector: str, timeout: int = 4000) -> bool:
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def try_fill(self, selector: str, value: str, timeout: int = 3000) -> bool:
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception:
            return False
