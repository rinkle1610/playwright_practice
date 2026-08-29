import csv
import os
import sys
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "output.csv")
HEADLESS = os.environ.get("HEADLESS", "1") not in ("0", "false", "False")
ROW_LIMIT = int(os.environ.get("LIMIT", "0") or 0)

PRODUCT_SELECTOR = "#gallery-layout-container .vtex-search-result-3-x-galleryItem"
LOAD_MORE_SELECTOR = "div.vtex-search-result-3-x-buttonShowMore a"
NOT_FOUND_SELECTOR = ".vtex-search-result-3-x-searchNotFound"
COOKIE_SELECTORS = [
    "#onetrust-accept-btn-handler",
    "button#onetrust-accept-btn-handler",
    "button:has-text('Acceptă tot')",
    "button:has-text('Accept all')",
]


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def accept_cookies(page):
    for selector in COOKIE_SELECTORS:
        button = page.locator(selector)
        try:
            if button.count() and button.first.is_visible():
                button.first.click(timeout=2000)
                page.wait_for_timeout(500)
                return
        except PlaywrightTimeoutError:
            continue


def attach_search_listener(page, state):
    """Capture recordsFiltered from VTEX productSearchV3 (true listing total)."""

    def on_response(response):
        if "operationName=productSearchV3" not in response.url:
            return
        try:
            payload = response.json()
            product_search = (payload.get("data") or {}).get("productSearch") or {}
            records = product_search.get("recordsFiltered")
            if records is None:
                return
            previous = state.get("recordsFiltered")
            state["recordsFiltered"] = (
                records if previous is None else max(previous, records)
            )
        except Exception:
            return

    page.on("response", on_response)
    return on_response


def wait_for_listing_total(page, state, timeout_ms=25000):
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        if state.get("recordsFiltered") is not None:
            return
        if page.locator(NOT_FOUND_SELECTOR).count() > 0:
            if state.get("recordsFiltered") is None:
                state["recordsFiltered"] = 0
            return
        page.wait_for_timeout(250)


def load_all_products(page):
    """Click 'Arată mai mult' until it disappears, then count gallery items."""
    previous_count = page.locator(PRODUCT_SELECTOR).count()

    for _ in range(80):
        load_more = page.locator(LOAD_MORE_SELECTOR)
        if load_more.count() == 0:
            break
        try:
            if not load_more.first.is_visible():
                break
        except Exception:
            break

        current_count = page.locator(PRODUCT_SELECTOR).count()
        try:
            load_more.first.scroll_into_view_if_needed()
            load_more.first.click(timeout=8000, no_wait_after=True)
        except PlaywrightTimeoutError:
            break

        try:
            page.wait_for_function(
                """([selector, oldCount]) =>
                    document.querySelectorAll(selector).length > oldCount""",
                arg=[PRODUCT_SELECTOR, current_count],
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            page.wait_for_timeout(1500)
            if page.locator(PRODUCT_SELECTOR).count() <= current_count:
                break

        new_count = page.locator(PRODUCT_SELECTOR).count()
        if new_count == previous_count:
            break
        previous_count = new_count

    return page.locator(PRODUCT_SELECTOR).count()


def count_products_on_page(page, page_url):
    state = {"recordsFiltered": None}
    listener = attach_search_listener(page, state)

    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        accept_cookies(page)

        try:
            page.wait_for_selector(
                f"{PRODUCT_SELECTOR}, {NOT_FOUND_SELECTOR}",
                timeout=20000,
            )
        except PlaywrightTimeoutError:
            pass

        wait_for_listing_total(page, state, timeout_ms=20000)

        if state.get("recordsFiltered") is not None:
            return int(state["recordsFiltered"])

        if page.locator(NOT_FOUND_SELECTOR).count() > 0:
            return 0

        return int(load_all_products(page))
    finally:
        try:
            page.remove_listener("response", listener)
        except Exception:
            pass


def process_csv(input_file):
    with open(input_file, "r", newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames or "Page URL" not in fieldnames:
        raise ValueError("CSV must contain a 'Page URL' column.")
    if "Total" not in fieldnames:
        raise ValueError("CSV must contain a 'Total' column.")

    if ROW_LIMIT:
        rows_to_process = rows[:ROW_LIMIT]
    else:
        rows_to_process = rows

    with sync_playwright() as playwright:
        launch_kwargs = {"headless": HEADLESS}
        try:
            browser = playwright.chromium.launch(channel="chrome", **launch_kwargs)
        except Exception:
            browser = playwright.chromium.launch(**launch_kwargs)

        context = browser.new_context(
            locale="ro-RO",
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()

        try:
            for row_number, row in enumerate(rows_to_process, start=1):
                page_url = (row.get("Page URL") or "").strip()
                print("\n" + "=" * 70)
                print(f"Row: {row_number}/{len(rows_to_process)}")
                print(f"Page URL: {page_url}")
                print("=" * 70)

                if not page_url:
                    print("Empty Page URL. Skipping.")
                    continue

                for attempt in range(1, 3):
                    try:
                        if page.is_closed():
                            page = context.new_page()
                        total = count_products_on_page(page, page_url)
                        row["Total"] = total
                        print(f"Total updated to: {total}")
                        break
                    except Exception as error:
                        print(f"ERROR (attempt {attempt}): {error}")
                        try:
                            page.close()
                        except Exception:
                            pass
                        try:
                            context.close()
                        except Exception:
                            pass
                        context = browser.new_context(
                            locale="ro-RO",
                            viewport={"width": 1400, "height": 900},
                        )
                        page = context.new_page()
                        if attempt == 2:
                            print("Keeping original Total for this row.")

                write_csv(OUTPUT_FILE, fieldnames, rows)
        finally:
            browser.close()

    print("\n" + "=" * 70)
    print("Scraping completed.")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("python terminal_of_fashion.py input.csv")
        sys.exit(1)

    process_csv(sys.argv[1])
