from playwright.sync_api import sync_playwright
from security_scanner import scan_page

import json


BASE_URL = "http://127.0.0.1:5500/website/"

PAGES = [
    "index.html",
    "login.html",
    "signup.html",
    "products.html"
]


def print_page_report(
    page_name,
    report
):

    print(
        "\n" + "=" * 60
    )

    print(
        f"🛡️ {page_name.upper()}"
    )

    print(
        "=" * 60
    )

    print(
        f"URL: {report['url']}"
    )

    print(
        f"Title: {report['title']}"
    )

    print(
        f"Links: {report['links']}"
    )

    print(
        f"Forms: {report['forms']}"
    )

    print(
        f"Inputs: {report['inputs']}"
    )

    print(
        f"Buttons: {report['buttons']}"
    )

    print(
        f"Scripts: {report['scripts']}"
    )

    print(
        f"Inline handlers: "
        f"{report['inline_handlers']}"
    )

    print(
        "\n🚨 FINDINGS:"
    )

    if not report["findings"]:

        print(
            "✅ No findings."
        )

    else:

        for index, finding in enumerate(
            report["findings"],
            start=1
        ):

            print(
                f"{index}. "
                f"[{finding['severity']}] "
                f"{finding['type']} - "
                f"{finding['message']}"
            )


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    all_reports = []

    all_findings = []


    # ========================================================
    # SCAN EVERY PAGE
    # ========================================================

    for page_name in PAGES:

        url = BASE_URL + page_name

        print(
            f"\n🔍 Scanning: {url}"
        )

        try:

            page.goto(
                url,
                wait_until="load"
            )

            report = scan_page(
                page
            )

            all_reports.append(
                report
            )

            for finding in report["findings"]:

                finding_copy = finding.copy()

                finding_copy["page"] = page_name

                all_findings.append(
                    finding_copy
                )

            print_page_report(
                page_name,
                report
            )


        except Exception as error:

            print(
                f"\n❌ Could not scan "
                f"{page_name}: {error}"
            )


    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n\n" + "=" * 60
    )

    print(
        "🏆 COMPLETE WEB AUDIT"
    )

    print(
        "=" * 60
    )


    print(
        f"\nPages scanned: "
        f"{len(all_reports)}"
    )

    print(
        f"Total findings: "
        f"{len(all_findings)}"
    )


    # ========================================================
    # SEVERITY COUNTS
    # ========================================================

    severity_counts = {

        "HIGH": 0,

        "MEDIUM": 0,

        "LOW": 0,

        "INFO": 0
    }


    for finding in all_findings:

        severity = finding.get(
            "severity",
            "INFO"
        )

        if severity in severity_counts:

            severity_counts[severity] += 1


    print(
        "\n📊 SEVERITY SUMMARY"
    )

    print(
        f"HIGH:   {severity_counts['HIGH']}"
    )

    print(
        f"MEDIUM: {severity_counts['MEDIUM']}"
    )

    print(
        f"LOW:    {severity_counts['LOW']}"
    )

    print(
        f"INFO:   {severity_counts['INFO']}"
    )


    # ========================================================
    # ALL FINDINGS
    # ========================================================

    print(
        "\n🚨 ALL FINDINGS"
    )


    if not all_findings:

        print(
            "✅ No security findings detected."
        )

    else:

        for index, finding in enumerate(
            all_findings,
            start=1
        ):

            print(
                f"\n{index}. "
                f"[{finding['severity']}] "
                f"{finding['type']}"
            )

            print(
                f"   Page: "
                f"{finding['page']}"
            )

            print(
                f"   {finding['message']}"
            )


    # ========================================================
    # SAVE JSON REPORT
    # ========================================================

    final_report = {

        "pages_scanned":
            len(all_reports),

        "total_findings":
            len(all_findings),

        "severity_summary":
            severity_counts,

        "reports":
            all_reports,

        "findings":
            all_findings
    }


    report_file = (
        "agent/security_report.json"
    )


    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_report,
            file,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"\n💾 Report saved: "
        f"{report_file}"
    )


    input(
        "\nPress ENTER to close browser..."
    )


    browser.close()
    