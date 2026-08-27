from playwright.sync_api import sync_playwright

url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(url)

    # Title
    title = page.locator("div.product_main h1").inner_text()

    # Price
    price = page.locator("div.product_main .price_color").inner_text()

    # Stock
    stock = page.locator("div.product_main .availability").inner_text().strip()

    # Product Description
    description = page.locator("#product_description + p").inner_text()

    # Product Information
    information = {}

    rows = page.locator("table.table-striped tr")

    for i in range(rows.count()):
        row = rows.nth(i)

        key = row.locator("th").inner_text().strip()
        value = row.locator("td").inner_text().strip()

        information[key] = value

    # Print the results
    print("=" * 60)
    print("PRODUCT DETAILS")
    print("=" * 60)

    print("Title:", title)
    print("Price:", price)
    print("Stock:", stock)

    print("\nProduct Description:")
    print(description)

    print("\nProduct Information:")
    for key, value in information.items():
        print(f"{key}: {value}")

    browser.close()
