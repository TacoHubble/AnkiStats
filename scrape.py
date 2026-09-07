import os
import json
import re
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("ANKIWEB_USER")
PASSWORD = os.environ.get("ANKIWEB_PASS")

# Exact titles of your add-ons as they appear on your dashboard
TRACKED_TITLES = [
    "Edit While Reviewing 🚀",
    "Generic-to-Brand Names (With AnkiMobile/AnkiDroid Support)",
]

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Log in
        page.goto("https://ankiweb.net/account/login")
        page.fill("input[type='email'], input[name='username']", USERNAME)
        page.fill("input[type='password'], input[name='password']", PASSWORD)
        page.click("button[type='submit'], input[type='submit']")
        page.wait_for_load_state("networkidle")

        # 2. Open dashboard
        page.goto("https://ankiweb.net/shared/mine")
        page.wait_for_selector("table")

        rows = page.query_selector_all("table tr")
        addon_counts = {}
        total_downloads = 0

        for row in rows:
            cells = [c.inner_text().strip() for c in row.query_selector_all("td")]
            if len(cells) >= 5:
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

        print(f"Success! Total downloads: {total_downloads}")

if __name__ == "__main__":
    run()
