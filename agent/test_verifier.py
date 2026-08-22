from playwright.sync_api import sync_playwright

from verifier import verify_workflow


START_URL = "http://127.0.0.1:5500/website/"


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(START_URL)

    print("🌐 Home page opened.")

    page.get_by_role(
        "link",
        name="Login"
    ).click()

    print("🖱️ Login clicked.")

    result = verify_workflow(
        page,
        "Navigate to Login page"
    )

    print("\n🔍 VERIFICATION RESULT:\n")

    print(result)

    input(
        "\nPress ENTER to close..."
    )

    browser.close()
