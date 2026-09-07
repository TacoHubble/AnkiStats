import os
import json
import re
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("ANKIWEB_USER", "").strip()
PASSWORD = os.environ.get("ANKIWEB_PASS", "").strip()

TRACKED_TITLES = [
    "Edit While Reviewing 🚀",
    "Generic-to-Brand Names (With AnkiMobile/AnkiDroid Support)",
]

def run():
    if not USERNAME or not PASSWORD:
        raise ValueError("Missing ANKIWEB_USER or ANKIWEB_PASS environment variables.")

    with sync_playwright() as p:
        # Launch Chromium with a standard browser User-Agent
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 1. Navigate to login
        page.goto("https://ankiweb.net/account/login", wait_until="domcontentloaded")

        # 2. Wait for form elements and fill credentials
        # AnkiWeb uses id="username" or form input elements inside .form-control
        page.wait_for_selector("input", timeout=15000)
        
        # Fill email / username
        user_input = page.locator("input#username, input[name='username'], input[type='email'], input.form-control").first
        user_input.fill(USERNAME)

        # Fill password
        pass_input = page.locator("input#password, input[name='password'], input[type='password']").first
        pass_input.fill(PASSWORD)

        # Submit form
        submit_btn = page.locator("button[type='submit'], input[type='submit']").first
        submit_btn.click()

        # Wait for navigation after submit
        page.wait_for_load_state("networkidle")

        # 3. Open shared dashboard
        page.goto("https://ankiweb.net/shared/mine", wait_until="networkidle")
        page.wait_for_selector("table", timeout=15000)

        rows = page.query_selector_all("table tr")
        addon_counts = {}
        total_downloads = 0

        for row in rows:
            cells = [c.inner_text().strip() for c in row.query_selector_all("td")]
            if len(cells) >= 5:
                # Column structure: [Info, Title, Thumbs Up, Modified, Downloads, Anki]
                title = cells[1]
                downloads_raw = cells[4]

                if any(tracked.lower() in title.lower() for tracked in TRACKED_TITLES):
                    match = re.search(r"\d+", downloads_raw.replace(",", ""))
                    count = int(match.group(0)) if match else 0
                    addon_counts[title] = count
                    total_downloads += count

        browser.close()

        payload = {
            "total_downloads": total_downloads,
            "breakdown": addon_counts
        }

        with open("stats.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"Scrape successful! Total downloads: {total_downloads}")

if __name__ == "__main__":
    run()
