from playwright.sync_api import sync_playwright
from security_scanner import scan_website
import json

BASE_URL = "http://127.0.0.1:5500/website"

PAGES = [
    "index.html",
    "login.html",
    "signup.html",
    "products.html"
]

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    print("\n🛡️ STARTING COMPLETE SECURITY AUDIT...\n")

    report = scan_website(
        browser,
        BASE_URL,
        PAGES
    )

    print("\n" + "=" * 60)
    print("🏆 WEB AUDIT COMPLETE")
    print("=" * 60)

    print(
        f"\nPages scanned: {report['pages_scanned']}"
    )

    print(
        f"Total findings: {report['total_findings']}"
    )

    print("\n📊 SEVERITY SUMMARY")

    for severity, count in report["severity_summary"].items():
        print(f"{severity}: {count}")

    print("\n🚨 FINDINGS")

    for index, finding in enumerate(
        report["findings"],
        start=1
    ):

        print(
            f"\n{index}. "
            f"[{finding['severity']}] "
            f"{finding['type']}"
        )

        print(
            f"   Page: {finding['page']}"
        )

        print(
            f"   {finding['message']}"
        )

    with open(
        "agent/security_report.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        "\n💾 Report saved: "
        "agent/security_report.json"
    )

    input(
        "\nPress ENTER to close browser..."
    )

    browser.close()
