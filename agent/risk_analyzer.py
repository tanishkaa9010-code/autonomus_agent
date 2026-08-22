import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ============================================================
# RISK WEIGHTS
# ============================================================

SEVERITY_WEIGHTS = {
    "HIGH": 30,
    "MEDIUM": 15,
    "LOW": 2,
    "INFO": 0
}


# ============================================================
# RECOMMENDATIONS
# ============================================================

RECOMMENDATIONS = {

    "FORM": (
        "Use POST instead of GET when submitting "
        "passwords or other sensitive credentials."
    ),

    "SECURITY_HEADER": {
        "Content-Security-Policy": (
            "Add a Content-Security-Policy header "
            "to restrict unsafe script and resource execution."
        ),

        "X-Frame-Options": (
            "Add X-Frame-Options to reduce clickjacking risk."
        ),

        "X-Content-Type-Options": (
            "Add X-Content-Type-Options: nosniff."
        ),

        "Referrer-Policy": (
            "Add an explicit Referrer-Policy."
        )
    },

    "PASSWORD_FIELD": (
        "Configure password fields with an appropriate "
        "autocomplete attribute."
    ),

    "JAVASCRIPT": (
        "Move inline JavaScript into controlled external "
        "scripts and apply a restrictive CSP where possible."
    ),

    "STORAGE_LEAK": (
        "Avoid storing sensitive authentication tokens, API keys, or "
        "credentials in unencrypted Web Storage (localStorage/sessionStorage)."
    ),

    "COOKIE_FLAG": (
        "Set HttpOnly, Secure, and SameSite (Strict/Lax) flags on cookies "
        "to prevent XSS cookie theft and CSRF attacks."
    )
}


# ============================================================
# RECOMMENDATION GENERATOR
# ============================================================

def generate_recommendations(findings):

    recommendations = []

    seen = set()


    for finding in findings:

        finding_type = finding.get(
            "type",
            ""
        )

        message = finding.get(
            "message",
            ""
        )


        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        if finding_type == "FORM":

            recommendation = RECOMMENDATIONS[
                "FORM"
            ]

            if recommendation not in seen:

                recommendations.append(
                    recommendation
                )

                seen.add(
                    recommendation
                )


        # ----------------------------------------------------
        # SECURITY HEADERS
        # ----------------------------------------------------

        elif finding_type == "SECURITY_HEADER":

            for header, recommendation in RECOMMENDATIONS[
                "SECURITY_HEADER"
            ].items():

                if header in message:

                    if recommendation not in seen:

                        recommendations.append(
                            recommendation
                        )

                        seen.add(
                            recommendation
                        )


        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        elif finding_type == "PASSWORD_FIELD":

            if "autocomplete" in message.lower():

                recommendation = RECOMMENDATIONS[
                    "PASSWORD_FIELD"
                ]

                if recommendation not in seen:

                    recommendations.append(
                        recommendation
                    )

                    seen.add(
                        recommendation
                    )


        # ----------------------------------------------------
        # JAVASCRIPT
        # ----------------------------------------------------

        elif finding_type == "JAVASCRIPT":

            recommendation = RECOMMENDATIONS[
                "JAVASCRIPT"
            ]

            if recommendation not in seen:

                recommendations.append(
                    recommendation
                )

                seen.add(
                    recommendation
                )

        # ----------------------------------------------------
        # STORAGE LEAK
        # ----------------------------------------------------

        elif finding_type == "STORAGE_LEAK":

            recommendation = RECOMMENDATIONS.get("STORAGE_LEAK")

            if recommendation and recommendation not in seen:

                recommendations.append(recommendation)

                seen.add(recommendation)

        # ----------------------------------------------------
        # COOKIE FLAG
        # ----------------------------------------------------

        elif finding_type == "COOKIE_FLAG":

            recommendation = RECOMMENDATIONS.get("COOKIE_FLAG")

            if recommendation and recommendation not in seen:

                recommendations.append(recommendation)

                seen.add(recommendation)


    return recommendations


# ============================================================
# RISK SCORE
# ============================================================

def calculate_risk_score(findings):

    high_count = 0
    medium_count = 0
    low_count = 0

    for finding in findings:

        severity = finding.get(
            "severity",
            "INFO"
        ).upper()

        if severity == "HIGH":
            high_count += 1

        elif severity == "MEDIUM":
            medium_count += 1

        elif severity == "LOW":
            low_count += 1


    # ========================================================
    # RISK CONTRIBUTION
    # ========================================================

    high_score = min(
        high_count * 30,
        60
    )

    medium_score = min(
        medium_count * 15,
        30
    )

    low_score = min(
        low_count * 2,
        10
    )


    score = (
        high_score
        + medium_score
        + low_score
    )


    score = min(
        score,
        100
    )


    # ========================================================
    # RISK LEVEL
    # ========================================================

    if score >= 70:

        level = "HIGH"

    elif score >= 40:

        level = "MEDIUM"

    elif score > 0:

        level = "LOW"

    else:

        level = "SAFE"


    return score, level

# ============================================================
# TOP RISKS
# ============================================================

def get_top_risks(findings, limit=5):

    severity_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
        "INFO": 3
    }

    sorted_findings = sorted(
        findings,
        key=lambda finding: severity_order.get(
            finding.get("severity", "INFO").upper(),
            3
        )
    )

    top_risks = []

    for finding in sorted_findings[:limit]:

        top_risks.append({
            "severity": finding.get(
                "severity",
                "INFO"
            ),

            "type": finding.get(
                "type",
                "UNKNOWN"
            ),

            "page": finding.get(
                "page",
                ""
            ),

            "message": finding.get(
                "message",
                ""
            )
        })

    return top_risks

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

def generate_executive_summary(
    report,
    score,
    level
):

    pages = report.get(
        "pages_scanned",
        0
    )

    findings = report.get(
        "total_findings",
        0
    )

    severity = report.get(
        "severity_summary",
        {}
    )

    high = severity.get(
        "HIGH",
        0
    )

    medium = severity.get(
        "MEDIUM",
        0
    )

    low = severity.get(
        "LOW",
        0
    )

    info = severity.get(
        "INFO",
        0
    )


    if high > 0:

        priority_message = (
            "Immediate attention is recommended "
            "for the identified high-severity issues."
        )

    elif medium > 0:

        priority_message = (
            "The identified medium-severity issues "
            "should be addressed as a priority."
        )

    elif findings > 0:

        priority_message = (
            "The identified findings should be "
            "reviewed and remediated."
        )

    else:

        priority_message = (
            "No security findings were identified."
        )


    return (
        f"The website was audited across {pages} pages "
        f"and {findings} security findings were identified. "
        f"The overall risk level is {level} with a score of "
        f"{score}/100. "
        f"The assessment includes {high} high, "
        f"{medium} medium, {low} low, and {info} informational "
        f"findings. "
        f"{priority_message}"
    )

# ============================================================
# ANALYZE REPORT
# ============================================================

def analyze_report(report):

    findings = report.get(
        "findings",
        []
    )


    score, level = calculate_risk_score(
        findings
    )

    executive_summary = generate_executive_summary(
    report,
    score,
    level
    )


    recommendations = generate_recommendations(
        findings
    )
    top_risks = get_top_risks(
    findings,
    limit=5
    )


    severity_summary = report.get(
        "severity_summary",
        {}
    )


    analysis = {

        "risk_score": score,

        "risk_level": level,

        "executive_summary": executive_summary,

        "pages_scanned":
            report.get(
                "pages_scanned",
                0
            ),

        "total_findings":
            report.get(
                "total_findings",
                len(findings)
            ),

        "severity_summary":
            severity_summary,

        "top_risks":
        top_risks,

        "recommendations":
            recommendations
    }


    return analysis


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    REPORT_FILE = (
        "agent/security_report.json"
    )


    print(
        "\n📊 Loading security report..."
    )


    try:

        with open(
            REPORT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            report = json.load(
                file
            )


    except Exception as error:

        print(
            f"\n❌ Could not load report: "
            f"{error}"
        )

        raise SystemExit(1)


    analysis = analyze_report(
        report
    )


    print(
        "\n" + "=" * 60
    )

    print(
        "🛡️ WEB AUDIT RISK ANALYSIS"
    )

    print(
        "=" * 60
    )


    print(
        f"\nRisk Score: "
        f"{analysis['risk_score']}/100"
    )

    print(
        f"Risk Level: "
        f"{analysis['risk_level']}"
    )

    print(
        f"Pages Scanned: "
        f"{analysis['pages_scanned']}"
    )

    print(
        f"Total Findings: "
        f"{analysis['total_findings']}"
    )


    print(
        "\n📊 SEVERITY SUMMARY"
    )


    for severity, count in analysis[
        "severity_summary"
    ].items():

        print(
            f"{severity}: {count}"
        )

    # ========================================================
    # TOP RISKS
    # ========================================================

    print(
        "\n🚨 TOP RISKS"
    )

    for index, risk in enumerate(
        analysis["top_risks"],
        start=1
    ):

        print(
            f"\n{index}. "
            f"[{risk['severity']}] "
            f"{risk['type']}"
        )

        print(
            f"   Page: {risk['page']}"
        )

        print(
            f"   {risk['message']}"
        )


    print(
            "\n💡 RECOMMENDATIONS"
        )


    if not analysis[
            "recommendations"
        ]:

            print(
                "✅ No recommendations."
            )

    else:

            for index, recommendation in enumerate(
                analysis["recommendations"],
                start=1
            ):

                print(
                    f"{index}. "
                    f"{recommendation}"
                )


    # ========================================================
    # SAVE ANALYSIS
    # ========================================================

    output_file = (
        "agent/risk_analysis.json"
    )


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            analysis,
            file,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"\n💾 Risk analysis saved: "
        f"{output_file}"
    )