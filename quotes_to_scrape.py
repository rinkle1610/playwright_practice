from playwright.sync_api import sync_playwright
import csv
from urllib.parse import urljoin


START_URL = "https://quotes.toscrape.com/"
OUTPUT_FILE = "quotes.csv"


# =========================
# CSS SELECTORS
# =========================

QUOTE_SELECTOR = ".quote"
QUOTE_TEXT_SELECTOR = ".text"
AUTHOR_SELECTOR = ".author"
ABOUT_LINK_SELECTOR = "span a"
TAG_SELECTOR = ".tags .tag"
NEXT_PAGE_SELECTOR = ".next a"


def run():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        current_url = START_URL

        # Create CSV file
        with open(
            OUTPUT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "page_url",
                    "quote",
                    "author",
                    "about_link",
                    "tags"
                ]
            )

            writer.writeheader()

            # =========================
            # SCRAPE ALL PAGES
            # =========================

            while current_url:

                print(f"Scraping: {current_url}")

                page.goto(current_url)

                # Find all quotes on current page
                quotes = page.locator(QUOTE_SELECTOR)

                quote_count = quotes.count()

                print(f"Found {quote_count} quotes")

                # =========================
                # SCRAPE EACH QUOTE
                # =========================

                for i in range(quote_count):

                    quote = quotes.nth(i)

                    # Quote text
                    quote_text = quote.locator(
                        QUOTE_TEXT_SELECTOR
                    ).inner_text()

                    # Author
                    author = quote.locator(
                        AUTHOR_SELECTOR
                    ).inner_text()

                    # About link
                    about_link = quote.locator(
                        ABOUT_LINK_SELECTOR
                    ).get_attribute("href")

                    about_link = urljoin(
                        page.url,
                        about_link
                    )

                    # Tags
                    tags = quote.locator(
                        TAG_SELECTOR
                    ).all_inner_texts()

                    # Convert tags to comma-separated string
                    tags = ", ".join(tags)

                    # Write data to CSV
                    writer.writerow({
                        "page_url": page.url,
                        "quote": quote_text,
                        "author": author,
                        "about_link": about_link,
                        "tags": tags
                    })

                    print(
                        quote_text,
                        "|",
                        author,
                        "|",
                        tags
                    )

                # =========================
                # NEXT PAGE
                # =========================

                next_button = page.locator(
                    NEXT_PAGE_SELECTOR
                )

                if next_button.count() > 0:

                    next_url = next_button.get_attribute("href")

                    current_url = urljoin(
                        page.url,
                        next_url
                    )

                else:

                    current_url = None

        browser.close()

        print("\nScraping completed.")
        print(f"CSV file created: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()