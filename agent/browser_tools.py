from playwright.sync_api import Page


# ============================================================
# CLICK TEXT
# ============================================================

def click_text(page: Page, text: str):

    # ========================================================
    # SELF-HEALING TEST
    # ========================================================
    # Temporary test trigger.
    # Later, remove this block after self-healing is verified.
    # ========================================================

       # ========================================================
    # FIND ELEMENT
    # ========================================================

    locator = page.get_by_text(
        text,
        exact=True
    )

    if locator.count() == 0:
        raise Exception(
            f"Could not find clickable element: {text}"
        )

    # ========================================================
    # PREFER BUTTON
    # ========================================================

    button = page.get_by_role(
        "button",
        name=text,
        exact=True
    )

    if button.count() > 0:

        button.first.click()

        return f"Clicked button '{text}'"

    # ========================================================
    # PREFER LINK
    # ========================================================

    link = page.get_by_role(
        "link",
        name=text,
        exact=True
    )

    if link.count() > 0:

        link.first.click()

        return f"Clicked link '{text}'"

    # ========================================================
    # FALLBACK
    # ========================================================

    locator.first.click()

    return f"Clicked element '{text}'"


# ============================================================
# TYPE TEXT
# ============================================================

def type_text(
    page: Page,
    field: str,
    value: str
):

    locator = page.get_by_placeholder(
        field,
        exact=True
    )

    if locator.count() == 0:

        locator = page.get_by_label(
            field,
            exact=True
        )

    if locator.count() == 0:

        raise Exception(
            f"Could not find input field: {field}"
        )

    locator.first.fill(
        value
    )

    return f"Typed into '{field}'"


# ============================================================
# READ PAGE
# ============================================================

def read_page(page: Page):

    try:

        return page.locator(
            "body"
        ).inner_text()

    except Exception as error:

        return (
            f"Could not read page: {error}"
        )


# ============================================================
# SCREENSHOT
# ============================================================

def take_screenshot(
    page: Page,
    path: str
):

    page.screenshot(
        path=path,
        full_page=True
    )

    return path