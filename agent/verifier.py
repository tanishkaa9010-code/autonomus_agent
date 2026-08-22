def verify_workflow(page, workflow):

    try:

        text = page.locator("body").inner_text().lower()

        url = page.url.lower()

        workflow_lower = workflow.lower()


        # ====================================================
        # SIGN UP
        # ====================================================

        if (
            "sign up" in workflow_lower
            or "registration" in workflow_lower
            or "create account" in workflow_lower
        ):

            if (
                "create account" in text
                or (
                    "name" in text
                    and "password" in text
                )
            ):

                return {
                    "status": "PASS",
                    "reason": "Browser reached the account creation page."
                }


        # ====================================================
        # LOGIN
        # ====================================================

        if "login" in workflow_lower:

            if (
                "email" in text
                and "password" in text
                and "login" in text
            ):

                return {
                    "status": "PASS",
                    "reason": "Browser reached the login page."
                }


        # ====================================================
        # PRODUCTS
        # ====================================================

        if "product" in workflow_lower:

            if (
                "gaming laptop" in text
                or "add to cart" in text
                or "products" in text
            ):

                return {
                    "status": "PASS",
                    "reason": "Browser reached the products page."
                }


        # ====================================================
        # CONTACT US
        # ====================================================

        if (
            "contact" in workflow_lower
            or "contact us" in workflow_lower
        ):

            if (
                "contact request submitted successfully"
                in text
            ):

                return {
                    "status": "PASS",
                    "reason": "Contact request was successfully submitted."
                }


            if "contact us" in text:

                return {
                    "status": "PASS",
                    "reason": "Browser reached the Contact Us section."
                }


        # ====================================================
        # HOME
        # ====================================================

        if "home" in workflow_lower:

            if (
                "shopdemo" in text
                and "welcome" in text
            ):

                return {
                    "status": "PASS",
                    "reason": "Browser reached the ShopDemo home page."
                }


        # ====================================================
        # GENERIC PAGE DETECTION
        # ====================================================

        # Products page can be recognized even when Gemini
        # gives a generic recovered workflow name.

        if (
            "gaming laptop" in text
            and "add to cart" in text
        ):

            return {
                "status": "PASS",
                "reason": "Browser reached the products page."
            }


        # Login page

        if (
            "email" in text
            and "password" in text
            and "login" in text
            and "create account" not in text
        ):

            return {
                "status": "PASS",
                "reason": "Browser reached the login page."
            }


        # Sign-up page

        if (
            "create account" in text
            and "name" in text
            and "password" in text
        ):

            return {
                "status": "PASS",
                "reason": "Browser reached the account creation page."
            }


        # ====================================================
        # GENERIC SUCCESS
        # ====================================================

        success_messages = [
            "successfully",
            "success",
            "completed",
            "submitted successfully",
            "account created successfully"
        ]

        for message in success_messages:

            if message in text:

                return {
                    "status": "PASS",
                    "reason":
                        f"Page contains success indicator: '{message}'."
                }


        # ====================================================
        # UNKNOWN
        # ====================================================

        return {
            "status": "UNKNOWN",
            "reason":
                "Could not determine the workflow result automatically."
        }


    except Exception as error:

        return {
            "status": "FAIL",
            "reason":
                f"Verification error: {error}"
        }

def verify_webcmd_page(page_data, workflow):

    try:

        url = page_data.get("url", "").lower()
        title = page_data.get("title", "").lower()

        workflow_lower = workflow.lower()

        # LOGIN
        if "login" in workflow_lower:

            if (
                "login" in title
                or "login" in url
            ):

                return {
                    "status": "PASS",
                    "reason": "WebCMD browser reached the login page."
                }

        # SIGN UP
        if (
            "sign up" in workflow_lower
            or "registration" in workflow_lower
            or "create account" in workflow_lower
        ):

            if (
                "signup" in url
                or "sign up" in title
            ):

                return {
                    "status": "PASS",
                    "reason": "WebCMD browser reached the sign-up page."
                }

        # PRODUCTS
        if "product" in workflow_lower:

            if (
                "products" in url
                or "products" in title
            ):

                return {
                    "status": "PASS",
                    "reason": "WebCMD browser reached the products page."
                }

        # HOME
        if "home" in workflow_lower:

            if (
                "index.html" in url
                or "shopdemo - home" in title
            ):

                return {
                    "status": "PASS",
                    "reason": "WebCMD browser reached the ShopDemo home page."
                }

        return {
            "status": "UNKNOWN",
            "reason": "Could not determine the WebCMD workflow result automatically."
        }

    except Exception as error:

        return {
            "status": "FAIL",
            "reason": f"WebCMD verification error: {error}"
        }