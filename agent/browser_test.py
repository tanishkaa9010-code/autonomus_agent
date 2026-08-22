from playwright.sync_api import sync_playwright

from browser_tools import (
    click_text,
    type_text,
    read_page
)


START_URL = "http://127.0.0.1:5500/website/"

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(START_URL)

    print("🌐 Website opened.")

    click_text(page, "Sign Up")

    print("✅ Sign Up clicked.")

    type_text(
        page,
        "Enter your name",
        "Tanishka"
    )

    type_text(
        page,
        "Enter email",
        "test@example.com"
    )

    type_text(
        page,
        "Create password",
        "Password123"
    )

    click_text(
        page,
        "Create Account"
    )

    print("\n📄 RESULT:\n")

    print(
        read_page(page)
    )

browser.close()