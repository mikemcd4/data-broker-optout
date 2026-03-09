"""
CAPTCHA solving via 2captcha API.

Supports:
  - reCAPTCHA v2 (checkbox / invisible)
  - reCAPTCHA v3
  - hCaptcha

Sign up at https://2captcha.com — costs ~$3 per 1000 solves.
Add your API key to config.yaml:

  captcha_api_key: "YOUR_2CAPTCHA_KEY"

If no key is configured, CAPTCHA sites fall back to manual pause.
"""

import asyncio
from twocaptcha import TwoCaptcha


async def detect_and_solve(page, api_key: str) -> bool:
    """
    Detect the CAPTCHA type on the current page, solve it via 2captcha,
    and inject the token. Returns True if solved successfully.
    """
    solver = TwoCaptcha(api_key)
    url = page.url

    # --- hCaptcha ---
    hcaptcha_key = await _get_hcaptcha_key(page)
    if hcaptcha_key:
        print(f"      [CAPTCHA] hCaptcha detected — solving via 2captcha...")
        try:
            result = await asyncio.to_thread(
                solver.hcaptcha, sitekey=hcaptcha_key, url=url
            )
            token = result["code"]
            await _inject_hcaptcha(page, token)
            print(f"      [CAPTCHA] Solved.")
            return True
        except Exception as e:
            print(f"      [CAPTCHA] Solver error: {e}")
            return False

    # --- reCAPTCHA v2 ---
    recaptcha_key = await _get_recaptcha_key(page)
    if recaptcha_key:
        print(f"      [CAPTCHA] reCAPTCHA v2 detected — solving via 2captcha...")
        try:
            result = await asyncio.to_thread(
                solver.recaptcha, sitekey=recaptcha_key, url=url
            )
            token = result["code"]
            await _inject_recaptcha(page, token)
            print(f"      [CAPTCHA] Solved.")
            return True
        except Exception as e:
            print(f"      [CAPTCHA] Solver error: {e}")
            return False

    return False


async def _get_recaptcha_key(page) -> str | None:
    try:
        key = await page.evaluate("""
            () => {
                const el = document.querySelector('.g-recaptcha[data-sitekey], [data-sitekey]');
                if (el) return el.getAttribute('data-sitekey');
                const iframe = document.querySelector('iframe[src*="recaptcha"]');
                if (iframe) {
                    const m = iframe.src.match(/[?&]k=([^&]+)/);
                    if (m) return m[1];
                }
                return null;
            }
        """)
        return key or None
    except Exception:
        return None


async def _get_hcaptcha_key(page) -> str | None:
    try:
        key = await page.evaluate("""
            () => {
                const el = document.querySelector('.h-captcha[data-sitekey], [data-hcaptcha-sitekey]');
                if (el) return el.getAttribute('data-sitekey') || el.getAttribute('data-hcaptcha-sitekey');
                const iframe = document.querySelector('iframe[src*="hcaptcha"]');
                if (iframe) {
                    const m = iframe.src.match(/[?&]sitekey=([^&]+)/);
                    if (m) return m[1];
                }
                return null;
            }
        """)
        return key or None
    except Exception:
        return None


async def _inject_recaptcha(page, token: str):
    await page.evaluate(f"""
        (token) => {{
            // Set response in all known containers
            const selectors = [
                '#g-recaptcha-response',
                'textarea[name="g-recaptcha-response"]',
            ];
            for (const sel of selectors) {{
                const el = document.querySelector(sel);
                if (el) {{ el.value = token; el.style.display = 'block'; }}
            }}
            // Call callback if defined
            if (typeof grecaptcha !== 'undefined') {{
                try {{
                    const widgetId = Object.keys(grecaptcha).find(k => !isNaN(k));
                    if (widgetId !== undefined) grecaptcha.getResponse(widgetId);
                }} catch(e) {{}}
            }}
            // Fire any defined callback
            const el = document.querySelector('.g-recaptcha[data-callback]');
            if (el) {{
                const cb = el.getAttribute('data-callback');
                if (typeof window[cb] === 'function') window[cb](token);
            }}
        }}
    """, token)
    await page.wait_for_timeout(500)


async def _inject_hcaptcha(page, token: str):
    await page.evaluate(f"""
        (token) => {{
            const selectors = [
                'textarea[name="h-captcha-response"]',
                'textarea[name="g-recaptcha-response"]',
                '[name="h-captcha-response"]',
            ];
            for (const sel of selectors) {{
                const el = document.querySelector(sel);
                if (el) {{ el.value = token; }}
            }}
            // Fire callback if defined
            const el = document.querySelector('.h-captcha[data-callback]');
            if (el) {{
                const cb = el.getAttribute('data-callback');
                if (typeof window[cb] === 'function') window[cb](token);
            }}
        }}
    """, token)
    await page.wait_for_timeout(500)
