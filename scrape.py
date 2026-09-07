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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            # 1. Navigate to login
            page.goto("https://ankiweb.net/account/login", wait_until="domcontentloaded")
            
            # Wait a few seconds to let any JS challenge render
            page.wait_for_timeout(5000)

            # 2. Fill login form with broader selectors
            page.wait_for_selector("input", timeout=15000)
            
            user_input = page.locator("input#username, input[name='username'], input[type='email'], input.form-control, input").first
            user_input.fill(USERNAME)

            pass_input = page.locator("input#password, input[name='password'], input[type='password']").nth(1) if page.locator("input[type='password']").count() > 1 else page.locator("input#password, input[name='password'], input[type='password']").first
            pass_input.fill(PASSWORD)

            submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Log in'), button:has-text('Login')").first
            submit_btn.click()

            page.wait_for_load_state("networkidle")

            # 3. Navigate to dashboard
            page.goto("https://ankiweb.net/shared/mine", wait_until="networkidle")
            page.wait_for_selector("table", timeout=15000)

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

            payload = {
                "total_downloads": total_downloads,
                "breakdown": addon_counts
            }

            with open("stats.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            print(f"Scrape successful! Total downloads: {total_downloads}")

        except Exception as e:
            # Take a screenshot and save page content for debugging if it fails
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
