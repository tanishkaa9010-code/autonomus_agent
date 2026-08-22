import json
from datetime import datetime


RECOVERY_FILE = "agent/recovery_report.json"


def save_recovery_report(
    page,
    workflow,
    reason,
    failed_action=None
):

    report = {
        "timestamp": datetime.now().isoformat(),
        "url": page.url,
        "title": page.title(),
        "workflow": workflow,
        "failed_action": failed_action,
        "reason": reason,
        "page_content": page.locator("body").inner_text(),
        "status": "needs_recovery"
    }

    with open(
        RECOVERY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    return report