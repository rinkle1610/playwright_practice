from playwright.sync_api import sync_playwright
import csv
from urllib.parse import urljoin


BASE_URL = "https://books.toscrape.com/"
OUTPUT_FILE = "books.csv"


# =========================
# CSS SELECTORS
# =========================

BOOK_SELECTOR = "article.product_pod"
TITLE_SELECTOR = "h3 a"
PRICE_SELECTOR = ".price_color"
IMAGE_SELECTOR = "img.thumbnail"
STOCK_SELECTOR = ".availability"
NEXT_PAGE_SELECTOR = "li.next a"


def run():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        current_url = BASE_URL

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
                    "title",
                    "detail_url",
                    "price",
                    "image_url",
                    "stock"
                ]
            )

            writer.writeheader()

            while current_url:

                print(f"Scraping: {current_url}")

                page.goto(current_url)

                # Find all books on the page
                books = page.locator(BOOK_SELECTOR)

                book_count = books.count()

                print(f"Found {book_count} books")

                for i in range(book_count):

                    book = books.nth(i)

                    # -------------------------
                    # Title
                    # -------------------------

                    title = book.locator(
                        TITLE_SELECTOR
                    ).get_attribute("title")


                    # -------------------------
                    # Detail URL
                    # -------------------------

                    detail_url = book.locator(
                        TITLE_SELECTOR
                    ).get_attribute("href")

                    detail_url = urljoin(
                        page.url,
                        detail_url
                    )


                    # -------------------------
                    # Price
                    # -------------------------

                    price = book.locator(
                        PRICE_SELECTOR
                    ).inner_text()


                    # -------------------------
                    # Image URL
                    # -------------------------

                    image_url = book.locator(
                        IMAGE_SELECTOR
                    ).get_attribute("src")

                    image_url = urljoin(
                        page.url,
                        image_url
                    )


                    # -------------------------
                    # Stock
                    # -------------------------

                    stock = book.locator(
                        STOCK_SELECTOR
                    ).inner_text()


                    # -------------------------
                    # Write data to CSV
                    # -------------------------

                    writer.writerow({
                        "page_url": page.url,
                        "title": title,
                        "detail_url": detail_url,
                        "price": price,
                        "image_url": image_url,
                        "stock": stock
                    })


                    print(
                        title,
                        price,
                        stock
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