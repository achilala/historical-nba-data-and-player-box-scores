"""Take screenshots of each tab in the NBA Analytics Dashboard."""
import subprocess
import time
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8501"

TABS = [
    ("Player Stats",   "docs/screenshot.png"),
    ("Player Profile", "docs/screenshot_player_profile.png"),
    ("Team Stats",     "docs/screenshot_team_stats.png"),
    ("Team History",   "docs/screenshot_team_history.png"),
]


def wait_for_app(page, timeout=60):
    print("Waiting for app to load...")
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=timeout * 1000)
    # Wait for spinners to disappear
    page.wait_for_function(
        "() => document.querySelectorAll('[data-testid=\"stSpinner\"]').length === 0",
        timeout=timeout * 1000,
    )
    time.sleep(2)


def take_screenshots(proc):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(URL)
        wait_for_app(page)

        for tab_label, output_path in TABS:
            print(f"  Screenshotting: {tab_label} -> {output_path}")
            tab = page.get_by_role("tab", name=tab_label)
            tab.click()
            # Wait for any spinners to clear after tab switch
            page.wait_for_function(
                "() => document.querySelectorAll('[data-testid=\"stSpinner\"]').length === 0",
                timeout=30000,
            )
            time.sleep(2)
            page.screenshot(path=output_path, full_page=False)

        browser.close()
    print("Done.")


def main():
    print("Starting Streamlit...")
    proc = subprocess.Popen(
        ["uv", "run", "streamlit", "run", "app.py",
         "--server.headless", "true",
         "--server.port", "8501"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(8)
        take_screenshots(proc)
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
