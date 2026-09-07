import os
import json
import re
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("ANKIWEB_USER", "").strip()
PASSWORD = os.environ.get("ANKIWEB_PASS", "").strip()

# Explicitly tracked add-ons
TRACKED_TITLES = [
    "Edit While Reviewing 🚀",
    "Gamepad/Controller Mapper",
    "Generic-to-Brand Names (With AnkiMobile/AnkiDroid Support)",
    "PeerNotes: Collaborative Flashcard Notes",
    "Placeholder",
]

def run():
    if not USERNAME or not PASSWORD:
        raise ValueError("Missing ANKIWEB_USER or ANKIWEB_PASS environment variables.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            # 1. Login
            page.goto("https://ankiweb.net/account/login", wait_until="networkidle")

            email_input = page.locator("input[placeholder='Email'], input[autocomplete='username'], input[type='text']").first
            password_input = page.locator("input[placeholder='Password'], input[type='password']").first

            email_input.wait_for(state="visible", timeout=15000)
            email_input.click()
            email_input.press_sequentially(USERNAME, delay=30)

            password_input.click()
            password_input.press_sequentially(PASSWORD, delay=30)

            submit_btn = page.locator("button:has-text('Log In'), button[type='submit']").first
            submit_btn.wait_for(state="visible", timeout=5000)

            with page.expect_navigation(url=lambda u: "account/login" not in u, timeout=20000):
                submit_btn.click()

            # 2. Shared Dashboard
            page.goto("https://ankiweb.net/shared/mine", wait_until="networkidle")
            page.wait_for_selector("table", timeout=15000)

            rows = page.query_selector_all("table tr")
            item_counts = {}
            total_downloads = 0

            for row in rows:
                cells = [c.inner_text().strip() for c in row.query_selector_all("td")]
                if len(cells) >= 5:
                    title = cells[1]
                    downloads_raw = cells[4]

                    # Match tracked titles (case-insensitive substring/equality)
                    if any(tracked.strip().lower() in title.strip().lower() for tracked in TRACKED_TITLES):
                        match = re.search(r"\d+", downloads_raw.replace(",", ""))
                        count = int(match.group(0)) if match else 0
                        item_counts[title] = count
                        total_downloads += count

            payload = {
                "total_downloads": total_downloads,
                "breakdown": item_counts
            }

            # Write clean UTF-8 output
            with open("stats.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            print(f"Scrape successful! Total downloads: {total_downloads}")

        except Exception as e:
            os.makedirs("debug", exist_ok=True)
            page.screenshot(path="debug/error_screenshot.png", full_page=True)
            with open("debug/error_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("Captured debug screenshot and HTML.")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
