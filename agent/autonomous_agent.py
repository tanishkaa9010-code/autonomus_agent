import os
import sys
import json
from google import genai
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from browser_tools import click_text, type_text, read_page, take_screenshot
from webcmd_tools import (
    create_session,
    close_session,
    run_webcmd,
    webcmd_click,
    webcmd_type,
    webcmd_snapshot,
    webcmd_navigate,
    webcmd_current_page,
    webcmd_read_dom,
    webcmd_screenshot
)

from verifier import (
    verify_workflow,
    verify_webcmd_page
)

from memory_tools import find_compatible_workflow

from recovery import save_recovery_report

# ============================================================
# GEMINI
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Gemini API key not found.")
    exit()

client = genai.Client(api_key=api_key)

print("🧠 Gemini connected.")


# ============================================================
# CONFIG
# ============================================================
import json
import os

START_URL = os.getenv(
    "WEB_AUDITOR_URL",
    "http://127.0.0.1:5500/website/index.html"
)
MEMORY_FILE = "agent/workflow_memory.json"


# ============================================================
# SELF-HEALING PLANNER
# ============================================================


def recover_workflow(page, failed_plan, failed_action, error):

    print("\n🩹 SELF-HEALING: ANALYZING FAILURE...")

    current_page = read_page(page)

    recovery_prompt = f"""
You are recovering a failed browser workflow.

FAILED WORKFLOW:
{json.dumps(failed_plan, indent=2)}

FAILED ACTION:
{json.dumps(failed_action, indent=2)}

ERROR:
{error}

CURRENT URL:
{page.url}

CURRENT PAGE:
{current_page}

Find another way to complete the SAME intended workflow.

Rules:

1. Use only elements currently visible on the page.
2. Do not invent elements.
3. Use exact visible text.
4. Return ONLY valid JSON.
5. Allowed tools:
   click
   type
   read

Format:

{{
    "workflow": "recovered workflow",
    "actions": [
        {{
            "tool": "click",
            "value": "exact visible text"
        }}
    ]
}}
"""

    try:


        response = client.models.generate_content(
            model="gemini-3.6-flash", contents=recovery_prompt
        )

        raw = response.text.strip()

        if raw.startswith("```"):

            raw = raw.replace("```json", "")

            raw = raw.replace("```", "")

            raw = raw.strip()

        recovered_plan = json.loads(raw)

        # ========================================================
        # VALIDATE RECOVERED PLAN
        # ========================================================

        for recovered_action in recovered_plan.get("actions", []):

            tool = recovered_action.get("tool")

            if tool == "click":
                value = recovered_action.get("value", "")

                count = page.get_by_text(
                    value,
                    exact=True
                ).count()

                if count == 0:
                    raise ValueError(
                        f"Recovery proposed invalid click target: '{value}'"
                    )

            elif tool == "type":
                field = recovered_action.get("field", "")

                count = page.get_by_placeholder(
                    field,
                    exact=True
                ).count()

                if count == 0:
                    count = page.get_by_label(
                        field,
                        exact=True
                    ).count()

                if count == 0:
                    raise ValueError(
                        f"Recovery proposed invalid field: '{field}'"
                    )

            elif tool == "read":
                continue

            else:
                raise ValueError(
                    f"Recovery proposed unknown tool: '{tool}'"
                )

        print("\n🧠 RECOVERED PLAN:\n")

        print(
            json.dumps(
                recovered_plan,
                indent=2,
                ensure_ascii=False
            )
        )

        return recovered_plan

    except Exception as recovery_error:

        print("\n❌ SELF-HEALING PLANNER FAILED:")

        print(recovery_error)
        print("\n🔎 SEARCHING MEMORY FOR RECOVERY WORKFLOW...")

        try:
            memory_file = "agent/workflow_memory.json"

            with open(memory_file, "r", encoding="utf-8") as file:
                memory = json.load(file)

            fallback_plan = find_compatible_workflow(
                page,
                memory.get("workflows", [])
            )

            if fallback_plan is not None:
                print("\n💾 MEMORY RECOVERY PLAN FOUND:\n")
                print(
                    json.dumps(
                        fallback_plan,
                        indent=2,
                        ensure_ascii=False
                    )
                )

                return fallback_plan

            print("\n⚠️ No compatible recovery workflow found.")

        except Exception as memory_error:
            print("\n❌ MEMORY RECOVERY FAILED:")
            print(memory_error)

        return None


# ============================================================
# START PLAYWRIGHT
# ============================================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    try:
        response = page.goto(
            START_URL,
            wait_until="commit",
            timeout=30000
        )

        print("🌐 Page navigation started.")

    except Exception as error:
        print(f"⚠️ Navigation warning: {error}")
        print("↪ Continuing with the loaded page...")
        # ========================================================
    # START WEBCMD
    # ========================================================

    print("\n🌐 Starting WebCMD...")

    webcmd_session = create_session()

    print(
        f"🆔 WebCMD session: {webcmd_session}"
    )

    try:

        webcmd_navigate(
            START_URL,
            webcmd_session
        )

    except Exception as error:
        print("⚠️ WebCMD navigation warning:")
        print(error)
        print("↪ Continuing with Playwright-loaded page...")

    print("✅ WebCMD connected to website.")


    print("🌐 Browser opened.")

    # ========================================================
    # READ WEBSITE
    # ========================================================

    website_text = read_page(page)

    print("\n📄 WEBSITE:\n")

    print(website_text)

    # ========================================================
    # LOAD MEMORY
    # ========================================================

    try:

        with open(MEMORY_FILE, "r", encoding="utf-8") as file:

            memory = json.load(file)

    except FileNotFoundError:

        memory = {"workflows": []}

    print(f"\n💾 Learned workflows: " f"{len(memory['workflows'])}")

    # ========================================================
    # VARIABLES
    # ========================================================

    plan = None

    using_memory = False

    action_failed = False

    # ========================================================
    # GEMINI PLANNING
    # ========================================================

    try:

        # ----------------------------------------------------
        # TEMPORARY TEST
        # ----------------------------------------------------
        # This intentionally forces Gemini fallback.
        #
        # REMOVE THESE TWO LINES AFTER SELF-HEALING TEST.
        # ----------------------------------------------------

        prompt = f"""
You are an autonomous browser testing agent.

Website URL:
{START_URL}

Visible website content:
{website_text}

Previously learned workflows:
{json.dumps(memory, indent=2)}

Choose ONE useful workflow to test.

Return ONLY valid JSON.

Format:

{{
    "workflow": "name",
    "actions": [
        {{
            "tool": "click",
            "value": "exact visible text"
        }}
    ]
}}

Allowed tools:

click
type
read

For type:

{{
    "tool": "type",
    "field": "exact placeholder",
    "value": "text"
}}

Rules:

1. Only use elements visible on the current page.
2. Do not invent elements.
3. Keep the workflow simple.
4. Prefer useful user workflows.
"""

        print("\n🧠 Asking Gemini for an action plan...")


        response = client.models.generate_content(
            model="gemini-3.6-flash", contents=prompt
        )

        raw = response.text.strip()

        print("\n🤖 GEMINI RAW RESPONSE:\n")

        print(raw)

        if raw.startswith("```"):

            raw = raw.replace("```json", "")

            raw = raw.replace("```", "")

            raw = raw.strip()

        plan = json.loads(raw)

        print("\n✅ GEMINI PLAN:\n")

        print(json.dumps(plan, indent=2))

    # ========================================================
    # GEMINI FAILURE → MEMORY
    # ========================================================

    except Exception as error:

        print("\n⚠️ Gemini unavailable.")

        print(f"Reason: {error}")

        print("\n🔎 SEARCHING MEMORY " "FOR COMPATIBLE WORKFLOW...")

        plan = find_compatible_workflow(page, memory["workflows"])

        if plan is None:

            print("\n⚠️ No compatible " "learned workflow found.")

            print("🛑 Agent will NOT blindly " "execute memory.")

            recovery_report = save_recovery_report(
                page=page,
                workflow="No compatible workflow",
                reason=str(error),
                failed_action=None,
            )

            print("\n🩹 RECOVERY REPORT CREATED:\n")

            print(json.dumps(recovery_report, indent=2))

            input("\nPress ENTER to close browser...")

            browser.close()

            exit()

        using_memory = True

        print("\n💾 COMPATIBLE WORKFLOW FOUND:\n")

        print(json.dumps(plan, indent=2))

    # ========================================================
    # EXECUTE PLAN
    # ========================================================

    print("\n🤖 EXECUTING PLAN...\n")

    for action in plan["actions"]:

        tool = action.get("tool")

        try:

            # ------------------------------------------------
            # CLICK
            # ------------------------------------------------

            if tool == "click":

                value = action.get("value", "")

                print(f"🖱️ Clicking: {value}")

                result = webcmd_click(
                        value,
                        webcmd_session
                    )

                print(
                        "   🌐 WebCMD executed the action."
                    )

                print(
                        json.dumps(
                            result,
                            indent=2,
                            ensure_ascii=False
                        )
                    )

                print(f"   ✅ {result}")

            # ------------------------------------------------
            # TYPE
            # ------------------------------------------------

            elif tool == "type":

                field = action.get("field", "")

                value = action.get("value", "")

                print(f"⌨️ Typing into: {field}")

                # Execute with WebCMD
                webcmd_res = webcmd_type(field, value, webcmd_session)
                print("   🌐 WebCMD typed into input.")

                # Sync with Playwright page
                try:
                    result = type_text(page, field, value)
                    print(f"   ✅ {result}")
                except Exception:
                    print("   ✅ Typed via WebCMD")

            # ------------------------------------------------
            # READ
            # ------------------------------------------------

            elif tool == "read":

                print("📖 Reading page...")

                result = read_page(page)

                print(result)

            else:

                print(f"⚠️ Unknown tool: {tool}")

                action_failed = True

                break

        # ====================================================
        # ACTION FAILURE
        # ====================================================

        except Exception as error:

            action_failed = True

            print(f"\n❌ ACTION FAILED: {error}")

            current_page = read_page(page)

            print("\n📄 PAGE AT FAILURE:\n")

            print(current_page)

            # ------------------------------------------------
            # SCREENSHOT
            # ------------------------------------------------

            screenshot_path = "agent_failure.png"

            take_screenshot(page, screenshot_path)

            print(f"\n📸 Screenshot saved: " f"{screenshot_path}")

            # ------------------------------------------------
            # RECOVERY REPORT
            # ------------------------------------------------

            recovery_report = save_recovery_report(
                page=page,
                workflow=plan["workflow"],
                reason=str(error),
                failed_action=action,
            )

            print("\n🩹 RECOVERY REPORT CREATED:\n")

            print(json.dumps(recovery_report, indent=2))

            # ------------------------------------------------
            # SELF HEALING
            # ------------------------------------------------

            recovered_plan = recover_workflow(page, plan, action, str(error))

            # ------------------------------------------------
            # EXECUTE RECOVERED PLAN
            # ------------------------------------------------

            if recovered_plan is not None:

                print("\n🤖 EXECUTING RECOVERED PLAN...")

                recovery_failed = False

                for recovered_action in recovered_plan["actions"]:

                    recovered_tool = recovered_action.get("tool")

                    try:

                        # ------------------------------------
                        # RECOVERED CLICK
                        # ------------------------------------

                        if recovered_tool == "click":

                            recovered_value = recovered_action.get("value", "")

                            print(
                                f"\n🩹 Retrying click with WebCMD: "
                                f"{recovered_value}"
                            )

                            result = webcmd_click(
                                recovered_value,
                                webcmd_session
                            )

                            print(
                                "   🌐 WebCMD recovery executed."
                            )

                            print(
                                json.dumps(
                                    result,
                                    indent=2,
                                    ensure_ascii=False
                                )
                            )

                        # ------------------------------------
                        # RECOVERED TYPE
                        # ------------------------------------

                        elif recovered_tool == "type":

                            recovered_field = recovered_action.get("field", "")
                            recovered_value = recovered_action.get("value", "")

                            print(
                                f"\n🩹 Retrying type with WebCMD: "
                                f"{recovered_field}"
                            )

                            # Use WebCMD for recovered typing
                            javascript = f"""
                        const locator = page.getByLabel(
                            {json.dumps(recovered_field)},
                            {{ exact: true }}
                        );

                        await locator.fill(
                            {json.dumps(recovered_value)}
                        );
                        """

                            result = run_webcmd(
                                javascript,
                                webcmd_session
                            )

                            print("   🌐 WebCMD recovery typing executed.")

                            print(
                                json.dumps(
                                    result,
                                    indent=2,
                                    ensure_ascii=False
                                )
                            )

                        # ------------------------------------
                        # RECOVERED READ
                        # ------------------------------------

                        elif recovered_tool == "read":

                            print("\n📖 Reading recovered page...")

                            print(read_page(page))

                        else:

                            print(f"⚠️ Unknown recovered tool: " f"{recovered_tool}")

                            recovery_failed = True

                            break

                    except Exception as recovery_error:

                        recovery_failed = True

                        print(f"\n❌ RECOVERY ACTION FAILED: " f"{recovery_error}")

                        break

                # --------------------------------------------
                # VERIFY RECOVERY
                # --------------------------------------------

                if not recovery_failed:

                    print("\n🔍 Verifying recovered workflow...")

                    recovery_page_data = webcmd_current_page(webcmd_session)

                    recovery_verification = verify_webcmd_page(
                        recovery_page_data,
                        recovered_plan["workflow"]
                    )

                    print("\n🤖 RECOVERY VERIFICATION:\n")

                    print(json.dumps(recovery_verification, indent=2))

                    if recovery_verification.get("status") == "PASS":

                        print("\n🎉 SELF-HEALING SUCCESSFUL!")

                        # ------------------------------------
                        # SAVE RECOVERED WORKFLOW
                        # ------------------------------------

                        recovered_exists = False

                        for workflow in memory["workflows"]:

                            if workflow.get("workflow") == recovered_plan["workflow"]:

                                recovered_exists = True

                                break

                        if not recovered_exists:

                            memory["workflows"].append(
                                {
                                    "workflow": recovered_plan["workflow"],
                                    "actions": recovered_plan["actions"],
                                }
                            )

                            with open(MEMORY_FILE, "w", encoding="utf-8") as file:

                                json.dump(memory, file, indent=2)

                            print("💾 Recovered workflow " "saved to memory.")

                    else:

                        print("\n⚠️ Recovered workflow " "failed verification.")

            else:

                print("\n⚠️ No recovered plan available.")

            # Important:
            # We intentionally DO NOT use break here.
            # Recovery has already been attempted.

        # ========================================================
        # FINAL PAGE — WEBCMD
        # ========================================================

        final_snapshot = webcmd_snapshot(
            webcmd_session
        )

        final_page = final_snapshot.get(
            "page",
            {}
        )

        print("\n📄 FINAL PAGE:\n")

        print(
            json.dumps(
                final_page,
                indent=2,
                ensure_ascii=False
            )
        )

    # ========================================================
    # FINAL VERIFICATION
    # ========================================================

    print("\n🔍 Verifying workflow locally...")

    if action_failed:

        verification_data = {
            "status": "FAIL",
            "reason": "Original browser action failed.",
        }

    else:

        verification_data = verify_webcmd_page(
            final_page,
            plan["workflow"]
        )
    print("\n🤖 VERIFICATION:\n")

    print(json.dumps(verification_data, indent=2))

    # ========================================================
    # MEMORY UPDATE
    # ========================================================

    if verification_data.get("status") == "PASS":

        print("\n💾 Workflow successful.")

        exists = False

        for workflow in memory["workflows"]:

            if workflow.get("workflow") == plan["workflow"]:

                exists = True

                break

        if not exists:

            memory["workflows"].append(
                {"workflow": plan["workflow"], "actions": plan["actions"]}
            )

            with open(MEMORY_FILE, "w", encoding="utf-8") as file:

                json.dump(memory, file, indent=2)

            print("🧠 NEW WORKFLOW LEARNED!")

        else:

            print("💾 Workflow already exists.")

    else:

        print("\n⚠️ Workflow failed.")

        print("Memory was not updated.")

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 60)

    if using_memory:

        print("📚 EXECUTED FROM MEMORY")

    else:

        print("🧠 EXECUTED FROM GEMINI")

    print("🏁 AGENT EXECUTION COMPLETE")

    print("=" * 60)

    # ========================================================
    # SECURITY AUDIT
    # ========================================================

    print("\n🛡️ STARTING SECURITY AUDIT...")

    try:

        from security_scanner import scan_website
        from explorer import explore_website

        print("\n🔎 DISCOVERING WEBSITE PAGES...")

        discovered_pages = explore_website(page)

        print(f"\n🔎 Discovered {len(discovered_pages)} pages.")

        audit_report = scan_website(
            browser,
            START_URL,
            discovered_pages
        )
        
        print("\n" + "=" * 60)

        print("🛡️ SECURITY AUDIT COMPLETE")

        print("=" * 60)

        print(f"\nPages scanned: " f"{audit_report['pages_scanned']}")

        print(f"Total findings: " f"{audit_report['total_findings']}")

        print("\n📊 SEVERITY SUMMARY")

        for severity, count in audit_report["severity_summary"].items():

            print(f"{severity}: {count}")

        print("\n🚨 SECURITY FINDINGS")

        for index, finding in enumerate(audit_report["findings"], start=1):

            print(
                f"{index}. "
                f"[{finding['severity']}] "
                f"{finding['type']} "
                f"- {finding['message']} "
                f"({finding['page']})"
            )

        # ----------------------------------------------------
        # SAVE AUDIT REPORT
        # ----------------------------------------------------

        with open("agent/security_report.json", "w", encoding="utf-8") as file:

            json.dump(audit_report, file, indent=2, ensure_ascii=False)

        print("\n💾 Security report saved:" " agent/security_report.json")

                # ========================================================
        # RISK ANALYSIS
        # ========================================================

        print(
            "\n📊 STARTING RISK ANALYSIS..."
        )

        try:

            from risk_analyzer import analyze_report

            analysis = analyze_report(
                audit_report
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

            print(
                "\n💡 RECOMMENDATIONS"
            )

            for index, recommendation in enumerate(
                analysis["recommendations"],
                start=1
            ):

                print(
                    f"{index}. "
                    f"{recommendation}"
                )

            with open(
                "agent/risk_analysis.json",
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
                "\n💾 Risk analysis saved:"
                " agent/risk_analysis.json"
            )

            # ========================================================
            # HTML REPORT GENERATION
            # ========================================================

            print(
                "\n🌐 GENERATING HTML AUDIT REPORT..."
            )

            try:

                from report_generator import generate_report

                generate_report()

                print(
                    "\n🌐 HTML audit report generated:"
                    " agent/web_audit_report.html"
                )

            except Exception as report_error:

                print(
                    "\n⚠️ HTML report generation failed:"
                )

                print(
                    report_error
                )

            

        except Exception as risk_error:

            print(
                "\n⚠️ Risk analysis failed:"
            )


            print(
                risk_error
            )

    except Exception as audit_error:

        print("\n⚠️ Security audit failed:")

        print(audit_error)

    # ========================================================
    # CLOSE BROWSER & WEBCMD
    # ========================================================

    input("\nPress ENTER to close browser...")

    try:
        close_session(webcmd_session)
        print("🌐 WebCMD session closed.")
    except Exception:
        pass

    browser.close()





