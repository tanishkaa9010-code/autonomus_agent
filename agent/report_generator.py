import json
import sys
from html import escape
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


SECURITY_REPORT = "agent/security_report.json"
RISK_REPORT = "agent/risk_analysis.json"
OUTPUT_FILE = "agent/web_audit_report.html"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(filename):

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# SEVERITY CLASS
# ============================================================

def severity_class(severity):

    return severity.lower()


# ============================================================
# GENERATE REPORT
# ============================================================

def generate_report():

    security = load_json(
        SECURITY_REPORT
    )

    risk = load_json(
        RISK_REPORT
    )

    findings = security.get(
        "findings",
        []
    )

    recommendations = risk.get(
        "recommendations",
        []
    )

    top_risks = risk.get(
        "top_risks",
        []
    )

    score = risk.get(
        "risk_score",
        0
    )

    level = risk.get(
        "risk_level",
        "UNKNOWN"
    )

    pages = risk.get(
        "pages_scanned",
        0
    )

    total = risk.get(
        "total_findings",
        0
    )

    executive_summary = risk.get(
        "executive_summary",
        ""
    )

    summary = risk.get(
        "severity_summary",
        {}
    )

    target_url = security.get(
        "base_url",
        risk.get(
            "base_url",
            "Unknown"
        )
    )

    scan_time = datetime.now().strftime(
        "%d %b %Y, %I:%M %p"
    )


    # ========================================================
    # FINDINGS HTML
    # ========================================================

    findings_html = ""

    for finding in findings:

        severity = escape(
            str(
                finding.get(
                    "severity",
                    "INFO"
                )
            )
        )

        finding_type = escape(
            str(
                finding.get(
                    "type",
                    "UNKNOWN"
                )
            )
        )

        message = escape(
            str(
                finding.get(
                    "message",
                    ""
                )
            )
        )

        page = escape(
            str(
                finding.get(
                    "page",
                    ""
                )
            )
        )

        findings_html += f"""
        <tr>
            <td>
                <span class="badge {severity_class(severity)}">
                    {severity}
                </span>
            </td>

            <td>{finding_type}</td>

            <td>{page}</td>

            <td>{message}</td>
        </tr>
        """


    # ========================================================
    # TOP RISKS HTML
    # ========================================================

    top_risks_html = ""

    for risk_item in top_risks:

        severity = escape(
            str(
                risk_item.get(
                    "severity",
                    "INFO"
                )
            )
        )

        finding_type = escape(
            str(
                risk_item.get(
                    "type",
                    "UNKNOWN"
                )
            )
        )

        page = escape(
            str(
                risk_item.get(
                    "page",
                    ""
                )
            )
        )

        message = escape(
            str(
                risk_item.get(
                    "message",
                    ""
                )
            )
        )

        top_risks_html += f"""
        <div class="risk-item">

            <div class="risk-item-header">

                <span class="badge {severity_class(severity)}">
                    {severity}
                </span>

                <strong>{finding_type}</strong>

            </div>

            <div class="risk-page">
                Page: {page}
            </div>

            <div class="risk-message">
                {message}
            </div>

        </div>
        """


    # ========================================================
    # RECOMMENDATIONS HTML
    # ========================================================

    recommendations_html = ""

    for recommendation in recommendations:

        recommendations_html += f"""
        <li>
            {escape(str(recommendation))}
        </li>
        """


    # ========================================================
    # HTML DOCUMENT
    # ========================================================

    html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>WEB-AUDITOR Report</title>


<style>

/* =========================================================
   GLOBAL
========================================================= */

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    padding: 0;

    background: #080d16;

    color: #e8ecf1;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height: 1.6;
}}

.container {{
    width: 92%;

    max-width: 1250px;

    margin: 40px auto;
}}


/* =========================================================
   HEADER
========================================================= */

header {{
    background: #0d1422;

    border: 1px solid #243047;

    border-radius: 18px;

    padding: 30px;

    margin-bottom: 25px;

    box-shadow:
        0 10px 30px rgba(0, 0, 0, 0.25);
}}

header h1 {{
    margin: 0;

    font-size: 32px;

    font-weight: 800;

    color: #ffffff;
}}

header p {{
    margin: 6px 0 0;

    color: #8996a8;

    font-size: 14px;
}}

.target-info {{
    margin-top: 20px;

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(250px, 1fr));

    gap: 12px;
}}

.target-box {{
    background: #101827;

    border: 1px solid #27344c;

    border-radius: 10px;

    padding: 13px 16px;
}}

.target-title {{
    color: #687587;

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 0.8px;

    font-weight: 700;
}}

.target-value {{
    margin-top: 4px;

    color: #7fc1ff;

    font-family: Consolas, monospace;

    font-size: 13px;

    word-break: break-all;
}}


/* =========================================================
   SCAN INFORMATION / METHOD
========================================================= */

.scan-method {{
    background: #0d1422;

    border: 1px solid #243047;

    border-radius: 14px;

    padding: 24px;

    margin-bottom: 25px;

    box-shadow:
        0 10px 30px rgba(0, 0, 0, 0.25);
}}

.scan-method h2 {{
    margin: 0 0 16px;

    font-size: 18px;

    color: #ffffff;
}}

.method-grid {{
    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));

    gap: 12px;
}}

.method-item {{
    display: flex;

    flex-direction: column;

    gap: 4px;

    padding: 15px;

    background: #101827;

    border: 1px solid #27324a;

    border-radius: 10px;

    transition:
        transform 0.2s ease,
        border-color 0.2s ease;
}}

.method-item:hover {{
    transform: translateY(-2px);

    border-color: #52617c;
}}

.method-label {{
    color: #687587;

    font-size: 11px;

    text-transform: uppercase;

    letter-spacing: 0.6px;

    font-weight: 700;
}}

.method-item strong {{
    color: #62b0ff;

    font-size: 14px;
}}


/* =========================================================
   DASHBOARD
========================================================= */

.dashboard {{
    margin-bottom: 25px;
}}

.cards {{
    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(165px, 1fr));

    gap: 16px;

    margin: 20px 0;
}}

.card {{
    background: #101827;

    border: 1px solid #27324a;

    border-radius: 14px;

    padding: 22px;

    text-align: center;

    transition:
        transform 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}}

.card:hover {{
    transform: translateY(-3px);

    border-color: #52617c;

    box-shadow:
        0 8px 20px rgba(0, 0, 0, 0.25);
}}

.card h3 {{
    margin: 0 0 12px;

    color: #8d99aa;

    font-size: 12px;

    font-weight: 700;

    text-transform: uppercase;

    letter-spacing: 0.8px;
}}

.card .value {{
    color: #ffffff;

    font-size: 30px;

    font-weight: 800;

    line-height: 1.2;
}}

.score-total {{
    color: #6f7c8d;

    font-size: 16px;

    font-weight: 600;
}}


/* =========================================================
   RISK SCORE
========================================================= */

.risk-label {{
    margin-top: 8px;

    font-size: 12px;

    font-weight: 800;

    letter-spacing: 1px;
}}

.risk-label.high {{
    color: #ff6b6b;
}}

.risk-label.medium {{
    color: #ffb84d;
}}

.risk-label.low {{
    color: #ffe066;
}}

.risk-label.info {{
    color: #62b0ff;
}}

.risk-bar {{
    width: 100%;

    height: 8px;

    margin: 14px 0 8px;

    background: #202b3d;

    border-radius: 10px;

    overflow: hidden;
}}

.risk-fill {{
    height: 100%;

    background: #ff5c5c;

    border-radius: 10px;

    transition: width 0.5s ease;
}}


/* =========================================================
   SEVERITY COLORS
========================================================= */

.value.high {{
    color: #ff6b6b;
}}

.value.medium {{
    color: #ffb84d;
}}

.value.low {{
    color: #ffe066;
}}

.value.info {{
    color: #62b0ff;
}}

.high-card {{
    border-color: #4b242a;
}}

.medium-card {{
    border-color: #4b391e;
}}

.low-card {{
    border-color: #4b461e;
}}

.info-card {{
    border-color: #243e5c;
}}


/* =========================================================
   SECTIONS
========================================================= */

section {{
    background: #0d1422;

    border: 1px solid #243047;

    border-radius: 14px;

    padding: 25px;

    margin: 22px 0;
}}

section h2 {{
    margin-top: 0;

    margin-bottom: 18px;

    color: #ffffff;

    font-size: 20px;
}}


/* =========================================================
   EXECUTIVE SUMMARY
========================================================= */

.executive-summary {{
    background: #101827;

    border-left: 4px solid #62b0ff;

    border-radius: 8px;

    padding: 16px;

    color: #b9c4d2;

    font-size: 14px;
}}


/* =========================================================
   FINDING CONTROLS
========================================================= */

.finding-controls {{
    display: flex;

    flex-direction: column;

    gap: 14px;

    margin: 20px 0 24px;
}}

#findingSearch {{
    width: 100%;

    padding: 13px 16px;

    background: #101827;

    color: #e8ecf1;

    border: 1px solid #27324a;

    border-radius: 10px;

    font-size: 14px;

    transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}}

#findingSearch::placeholder {{
    color: #687587;
}}

#findingSearch:focus {{
    outline: none;

    border-color: #62b0ff;

    box-shadow:
        0 0 0 3px rgba(98, 176, 255, 0.12);
}}


/* =========================================================
   FILTER BUTTONS
========================================================= */

.filter-buttons {{
    display: flex;

    flex-wrap: wrap;

    gap: 10px;

    margin: 0 !important;
}}

.filter {{
    padding: 9px 18px;

    background: #101827;

    color: #9ba7b4;

    border: 1px solid #2b3952;

    border-radius: 8px;

    font-size: 12px;

    font-weight: 700;

    letter-spacing: 0.5px;

    cursor: pointer;

    transition:
        transform 0.2s ease,
        background 0.2s ease,
        border-color 0.2s ease,
        color 0.2s ease,
        box-shadow 0.2s ease;
}}

.filter:hover {{
    transform: translateY(-2px);

    background: #182337;

    color: #ffffff;

    border-color: #52617c;

    box-shadow:
        0 5px 12px rgba(0, 0, 0, 0.3);
}}

.filter:active {{
    transform: translateY(0);
}}

.filter.active {{
    background: #1c3654;

    color: #7fc1ff;

    border-color: #62b0ff;

    box-shadow:
        0 0 10px rgba(98, 176, 255, 0.18);
}}

.high-filter {{
    color: #ff8585;
}}

.high-filter:hover,
.high-filter.active {{
    background: #4b1e25;

    color: #ff8585;

    border-color: #ff5c5c;
}}

.medium-filter {{
    color: #ffc46b;
}}

.medium-filter:hover,
.medium-filter.active {{
    background: #4b361c;

    color: #ffc46b;

    border-color: #ffb84d;
}}

.low-filter {{
    color: #ffe46b;
}}

.low-filter:hover,
.low-filter.active {{
    background: #4a431c;

    color: #ffe46b;

    border-color: #ffd65c;
}}

.info-filter {{
    color: #7fc1ff;
}}

.info-filter:hover,
.info-filter.active {{
    background: #1c3654;

    color: #7fc1ff;

    border-color: #62b0ff;
}}


/* =========================================================
   FINDINGS TABLE
========================================================= */

table {{
    width: 100%;

    border-collapse: collapse;

    background: #0d1422;

    border-radius: 10px;

    overflow: hidden;
}}

thead {{
    background: #151f31;
}}

th {{
    padding: 14px;

    color: #9eabbc;

    font-size: 11px;

    text-align: left;

    text-transform: uppercase;

    letter-spacing: 0.6px;

    border-bottom: 1px solid #27324a;
}}

td {{
    padding: 14px;

    color: #cbd3dd;

    font-size: 13px;

    border-bottom: 1px solid #1c2739;
}}

tbody tr {{
    transition: background 0.15s ease;
}}

tbody tr:hover {{
    background: #101827;
}}


/* =========================================================
   BADGES
========================================================= */

.badge {{
    display: inline-block;

    padding: 4px 9px;

    border-radius: 6px;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 0.5px;
}}

.badge.high {{
    background: #4b1e25;

    color: #ff8585;

    border: 1px solid #7a3039;
}}

.badge.medium {{
    background: #4b361c;

    color: #ffc46b;

    border: 1px solid #795722;
}}

.badge.low {{
    background: #4a431c;

    color: #ffe46b;

    border: 1px solid #756b24;
}}

.badge.info {{
    background: #1c3654;

    color: #7fc1ff;

    border: 1px solid #315b84;
}}


/* =========================================================
   TOP RISKS
========================================================= */

.risk-item {{
    background: #101827;

    border: 1px solid #27324a;

    border-left: 4px solid #ff5c5c;

    border-radius: 10px;

    padding: 16px;

    margin-bottom: 12px;

    transition:
        transform 0.2s ease,
        border-color 0.2s ease;
}}

.risk-item:hover {{
    transform: translateX(3px);

    border-color: #52617c;
}}

.risk-item:last-child {{
    margin-bottom: 0;
}}

.risk-item-header {{
    display: flex;

    align-items: center;

    gap: 10px;

    margin-bottom: 8px;
}}

.risk-page {{
    color: #7fc1ff;

    font-family: Consolas, monospace;

    font-size: 12px;

    margin-bottom: 6px;
}}

.risk-message {{
    color: #b9c4d2;

    font-size: 13px;
}}


/* =========================================================
   RECOMMENDATIONS
========================================================= */

ul {{
    padding-left: 22px;
}}

li {{
    margin-bottom: 10px;

    color: #cbd3dd;
}}

li::marker {{
    color: #62b0ff;
}}


/* =========================================================
   FOOTER
========================================================= */

.footer {{
    margin-top: 30px;

    padding: 20px;

    text-align: center;

    color: #667386;

    font-size: 12px;

    border-top: 1px solid #202b3d;
}}


/* =========================================================
   RESPONSIVE
========================================================= */

@media(max-width: 700px) {{

    .container {{
        width: 94%;

        margin: 20px auto;
    }}

    header {{
        padding: 22px;
    }}

    header h1 {{
        font-size: 25px;
    }}

    .cards {{
        grid-template-columns: 1fr 1fr;

        gap: 10px;
    }}

    .card {{
        padding: 16px;
    }}

    .card .value {{
        font-size: 24px;
    }}

    section {{
        padding: 18px;

        overflow-x: auto;
    }}

    table {{
        min-width: 650px;
    }}

    .filter {{
        padding: 8px 13px;

        font-size: 11px;
    }}

}}

</style>

</head>


<body>

<div class="container">


<!-- =====================================================
     HEADER
====================================================== -->

<header>

    <h1>
        🛡️ WEB-AUDITOR
    </h1>

    <p>
        Autonomous Web Security Audit Report
    </p>

    <div class="target-info">

        <div class="target-box">

            <div class="target-title">
                Target URL
            </div>

            <div class="target-value">
                {escape(str(target_url))}
            </div>

        </div>


        <div class="target-box">

            <div class="target-title">
                Scan Time
            </div>

            <div class="target-value">
                {escape(str(scan_time))}
            </div>

        </div>

    </div>

</header>


<!-- =====================================================
     DASHBOARD
====================================================== -->

<div class="dashboard">


<div class="cards">


    <!-- RISK SCORE -->

    <div class="card">

        <h3>
            Risk Score
        </h3>

        <div class="value">

            {score}

            <span class="score-total">
                /100
            </span>

        </div>

        <div class="risk-bar">

            <div
                class="risk-fill"
                style="width: {score}%"
            ></div>

        </div>

        <div class="risk-label {str(level).lower()}">
            {escape(str(level))}
        </div>

    </div>


    <!-- PAGES -->

    <div class="card">

        <h3>
            Pages Scanned
        </h3>

        <div class="value">
            {pages}
        </div>

    </div>


    <!-- FINDINGS -->

    <div class="card">

        <h3>
            Total Findings
        </h3>

        <div class="value">
            {total}
        </div>

    </div>


    <!-- HIGH -->

    <div class="card high-card">

        <h3>
            High
        </h3>

        <div class="value high">
            {summary.get("HIGH", 0)}
        </div>

    </div>


    <!-- MEDIUM -->

    <div class="card medium-card">

        <h3>
            Medium
        </h3>

        <div class="value medium">
            {summary.get("MEDIUM", 0)}
        </div>

    </div>


    <!-- LOW -->

    <div class="card low-card">

        <h3>
            Low
        </h3>

        <div class="value low">
            {summary.get("LOW", 0)}
        </div>

    </div>


    <!-- INFO -->

    <div class="card info-card">

        <h3>
            Info
        </h3>

        <div class="value info">
            {summary.get("INFO", 0)}
        </div>

    </div>


</div>

</div>


<!-- =====================================================
     SCAN INFORMATION
====================================================== -->

<section class="scan-method">

    <h2>
        ⚙️ Scan Information
    </h2>

    <div class="method-grid">

        <div class="method-item">
            <span class="method-label">🤖 AI Agent</span>
            <strong>Gemini</strong>
        </div>

        <div class="method-item">
            <span class="method-label">🌐 Browser Runtime</span>
            <strong>Playwright + WebCMD</strong>
        </div>

        <div class="method-item">
            <span class="method-label">🛡️ Audit Type</span>
            <strong>Passive & Interactive Security Scan</strong>
        </div>

        <div class="method-item">
            <span class="method-label">🔎 Discovery</span>
            <strong>Autonomous Page Discovery</strong>
        </div>

    </div>

</section>


<!-- =====================================================
     EXECUTIVE SUMMARY
====================================================== -->

<section>

    <h2>
        📋 Executive Summary
    </h2>

    <div class="executive-summary">

        {escape(str(executive_summary))}

    </div>

</section>


<!-- =====================================================
     SEVERITY SUMMARY
====================================================== -->

<section>

    <h2>
        📊 Severity Summary
    </h2>

    <div class="summary">

        <div class="summary-item">

            🔴 HIGH

            <span class="number" style="color:#ff6b6b;">
                {summary.get("HIGH", 0)}
            </span>

        </div>


        <div class="summary-item">

            🟠 MEDIUM

            <span class="number" style="color:#ffb84d;">
                {summary.get("MEDIUM", 0)}
            </span>

        </div>


        <div class="summary-item">

            🟡 LOW

            <span class="number" style="color:#ffe066;">
                {summary.get("LOW", 0)}
            </span>

        </div>


        <div class="summary-item">

            🔵 INFO

            <span class="number" style="color:#62b0ff;">
                {summary.get("INFO", 0)}
            </span>

        </div>

    </div>

</section>


<!-- =====================================================
     TOP RISKS
====================================================== -->

<section>

    <h2>
        🚨 Top Priority Issues
    </h2>

    {top_risks_html}

</section>


<!-- =====================================================
     FINDINGS
====================================================== -->

<section>

    <h2>
        🚨 Security Findings
    </h2>


    <div class="finding-controls">


        <input
            type="text"
            id="findingSearch"
            placeholder="🔍 Search findings..."
            onkeyup="filterFindings()"
        >


        <div class="filter-buttons">


            <button
                onclick="setSeverity('ALL', this)"
                class="filter active"
            >
                ALL
            </button>


            <button
                onclick="setSeverity('HIGH', this)"
                class="filter high-filter"
            >
                HIGH
            </button>


            <button
                onclick="setSeverity('MEDIUM', this)"
                class="filter medium-filter"
            >
                MEDIUM
            </button>


            <button
                onclick="setSeverity('LOW', this)"
                class="filter low-filter"
            >
                LOW
            </button>


            <button
                onclick="setSeverity('INFO', this)"
                class="filter info-filter"
            >
                INFO
            </button>


        </div>

    </div>


    <table id="findingsTable">

        <thead>

            <tr>

                <th>
                    Severity
                </th>

                <th>
                    Type
                </th>

                <th>
                    Page
                </th>

                <th>
                    Description
                </th>

            </tr>

        </thead>


        <tbody>

            {findings_html}

        </tbody>

    </table>

</section>


<!-- =====================================================
     RECOMMENDATIONS
====================================================== -->

<section>

    <h2>
        💡 Recommendations
    </h2>

    <ul>

        {recommendations_html}

    </ul>

</section>


<!-- =====================================================
     FOOTER
====================================================== -->

<div class="footer">

    Generated by WEB-AUDITOR

</div>


</div>


<!-- =====================================================
     JAVASCRIPT
====================================================== -->

<script>

let selectedSeverity = "ALL";


function setSeverity(severity, clickedButton) {{

    selectedSeverity = severity;


    document
        .querySelectorAll(".filter")
        .forEach(function(button) {{

            button.classList.remove("active");

        }});


    clickedButton.classList.add("active");


    filterFindings();

}}


function filterFindings() {{

    const search =
        document
            .getElementById("findingSearch")
            .value
            .toLowerCase();


    const rows =
        document.querySelectorAll(
            "#findingsTable tbody tr"
        );


    rows.forEach(function(row) {{

        const text =
            row.innerText.toLowerCase();


        const badge =
            row.querySelector(".badge");


        const severity =
            badge
                ? badge.innerText
                    .trim()
                    .toUpperCase()
                : "";


        const matchesSeverity =
            selectedSeverity === "ALL" ||
            severity === selectedSeverity;


        const matchesSearch =
            text.includes(search);


        row.style.display =
            matchesSeverity && matchesSearch
                ? ""
                : "none";

    }});

}}

</script>


</body>

</html>

"""


    # ========================================================
    # WRITE REPORT
    # ========================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            html
        )


    print(
        "\n✅ HTML report generated!"
    )

    print(
        f"📄 Report: {OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_report()