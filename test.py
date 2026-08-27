#test_playwright.py
from playwright.sync_api import sync_playwright

def run():
    #proxy_server = "http://139.99.135.148:3128"
    #proxy_server = ""
    url = "https://ollama.com/library/deepseek-r1"

    with sync_playwright() as p:
        # Launch Chromium headless with proxy
        browser = p.chromium.launch(headless=False)

        # Create context with Chromium-like user agent (optional)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=60000, wait_until="networkidle")
            title = page.title()
            print("Page Title:", title)
        except Exception as e:
            print("Error loading page:", e)

        browser.close()

if __name__ == "__main__":
    run()

