# data-broker-optout

Automatically submit opt-out / removal requests to **181 data broker websites** using a real browser (Playwright). Built from the opt-out list maintained by [IntelTechniques](https://inteltechniques.com/workbook.html).

---

## How it works

1. You provide your personal info once in a local `config.yaml` (never uploaded anywhere).
2. The tool opens a real browser window and visits each data broker's opt-out page.
3. For sites that support it, forms are filled and submitted automatically.
4. When a CAPTCHA, phone verification, or email confirmation is needed, the tool **pauses** and shows you instructions so you can complete that step manually.
5. All results are saved to `results.json`. Re-run with `--resume` to skip brokers already completed.

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Create your config

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your name, address, and email. This file is listed in `.gitignore` and will **not** be committed.

> **Tip:** Use a dedicated email address (e.g. a Gmail alias or SimpleLogin address) for opt-out confirmations so your main inbox isn't flooded.

### 3. Run

```bash
# Run all brokers (browser window visible — recommended)
python main.py run

# Skip brokers you've already completed
python main.py run --resume

# Target a single broker by name
python main.py run --only "BeenVerified"

# Headless mode (no window) — may fail on CAPTCHAs
python main.py run --headless
```

---

## Commands

| Command | Description |
|---|---|
| `python main.py run` | Submit opt-out requests |
| `python main.py run --resume` | Skip already-completed brokers |
| `python main.py run --only NAME` | Run a single broker |
| `python main.py list` | List all 181 brokers and their platforms |
| `python main.py status` | Show progress from `results.json` |

---

## Result statuses

| Status | Meaning |
|---|---|
| `submitted` | Form submitted — no further action needed |
| `email_required` | Submitted — check your email for a confirmation link |
| `phone_required` | Requires SMS/phone verification — completed manually |
| `manual_required` | Could not automate — browser left open for manual completion |
| `captcha_required` | CAPTCHA present — paused for manual solve |
| `failed` | Navigation or unexpected error |

---

## Supported platforms

| Platform | Sites |
|---|---|
| **BeenVerified** | BeenVerified, FreePhoneTracer, and others |
| **Intelius** | Intelius, Addresses.com, Infospace, and others |
| **Whitepages** | Whitepages, 411.com, and others |
| **Spokeo** | Spokeo |
| **PeopleFinders** | PeopleFinders and related sites |
| **InstantCheckmate** | InstantCheckmate |
| **records_removal** | 12 sites sharing the same opt-out platform |
| **generic** | 143 remaining brokers — form-fill attempted automatically |

---

## Tips

- **Run it again every few months.** Data brokers re-add listings periodically.
- **Email verification:** Many brokers send a confirmation link. Check your inbox after each run and click the links.
- **Whitepages** requires SMS phone verification — the tool opens the page and waits for you.
- **Spokeo** requires you to find your listing URL first — the tool opens the opt-out page and waits.
- Some sites use CAPTCHAs. The tool pauses automatically; just solve the CAPTCHA and press Enter.

---

## Data source

Opt-out URLs sourced from the **IntelTechniques Data Removal Workbook** at
https://inteltechniques.com/workbook.html (updated October 2024).

---

## Legal

This tool submits opt-out requests on your behalf using your own personal information. It does not scrape, collect, or redistribute anyone else's data. Use it only for your own information.
