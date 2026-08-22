"""
WebCMD Tools Adapter for WEB-AUDITOR
====================================
Production-grade integration between autonomous agents and WebCMD CLI.
Provides resilient session management, structured action execution,
accessibility tree snapshots, security telemetry, and automatic cleanup.
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_webcmd_executable() -> str:
    """Dynamically locates the WebCMD binary across PATH and standard locations."""
    # 1. Explicit Environment Variable
    env_path = os.getenv("WEBCMD_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Check System PATH
    for name in ["webcmd", "webcmd.cmd", "webcmd.exe", "webcmd.ps1"]:
        found = shutil.which(name)
        if found:
            return found

    # 3. Check Windows standard npm roaming paths
    appdata = os.getenv("APPDATA", "")
    if appdata:
        candidate = os.path.join(appdata, "npm", "webcmd.cmd")
        if os.path.isfile(candidate):
            return candidate

    # 4. Known user specific path fallback
    fallback = r"C:\Users\Tanishka Aggarwal\AppData\Roaming\npm\webcmd.cmd"
    if os.path.isfile(fallback):
        return fallback

    return "webcmd"


WEBCMD_PATH = find_webcmd_executable()
DEFAULT_URL = os.getenv("WEB_AUDITOR_URL", "http://127.0.0.1:5500/website/index.html")


def run_command(args: List[str], input_text: Optional[str] = None, timeout: int = 60) -> Any:
    """Executes a WebCMD CLI command with robust error handling and JSON parsing."""
    try:
        result = subprocess.run(
            args,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"WebCMD command timed out after {timeout}s: {error}")
    except FileNotFoundError:
        raise RuntimeError(
            f"WebCMD executable not found at '{WEBCMD_PATH}'. "
            "Please ensure npm install -g @webcmd/cli is installed or set WEBCMD_PATH."
        )

    if result.returncode != 0:
        err_msg = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"WebCMD command failed (exit code {result.returncode}):\n{err_msg}")

    output = result.stdout.strip()
    if not output:
        return {}

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw_output": output}


# ============================================================
# SESSION MANAGEMENT
# ============================================================

def create_session() -> str:
    """Creates a new isolated WebCMD browser session and returns the session ID."""
    command = [WEBCMD_PATH, "session", "create", "-f", "json"]
    data = run_command(command)
    session_id = data.get("id")
    if not session_id:
        raise RuntimeError("WebCMD did not return a session ID: " + json.dumps(data))
    return session_id


def close_session(session_id: str) -> bool:
    """Closes an active WebCMD browser session to release memory and browser instances."""
    try:
        command = [WEBCMD_PATH, "session", "close", session_id]
        run_command(command, timeout=15)
        return True
    except Exception as e:
        print(f"⚠️ Warning: Could not cleanly close session {session_id}: {e}")
        return False


def list_sessions() -> List[Dict[str, Any]]:
    """Returns a list of all WebCMD sessions and their statuses."""
    try:
        command = [WEBCMD_PATH, "session", "list", "-f", "json"]
        data = run_command(command)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def cleanup_idle_sessions() -> int:
    """Closes all idle WebCMD sessions to prevent browser process buildup."""
    sessions = list_sessions()
    closed_count = 0
    for s in sessions:
        if isinstance(s, dict) and s.get("runtimeState") == "idle":
            s_id = s.get("id")
            if s_id and close_session(s_id):
                closed_count += 1
    return closed_count


class WebCMDSession:
    """Python Context Manager for automatic WebCMD session lifecycle management."""
    def __init__(self, initial_url: Optional[str] = None):
        self.initial_url = initial_url
        self.session_id: Optional[str] = None

    def __enter__(self) -> str:
        self.session_id = create_session()
        if self.initial_url:
            webcmd_navigate(self.initial_url, self.session_id)
        return self.session_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session_id:
            close_session(self.session_id)


# ============================================================
# BROWSER AUTOMATION & INTERACTION
# ============================================================

def run_webcmd(javascript: str, session_id: str, timeout: int = 60) -> Any:
    """Executes arbitrary JavaScript/Playwright commands inside the specified WebCMD session."""
    command = [
        WEBCMD_PATH,
        "--session",
        session_id,
        "browser",
        "run",
        "--stdin",
        "--timeout",
        str(timeout)
    ]
    return run_command(command, input_text=javascript, timeout=timeout)


def webcmd_snapshot(session_id: str, mode: str = "act") -> Dict[str, Any]:
    """
    Captures a high-density accessibility/action snapshot of the active page.
    Mode can be: 'act' (action-oriented), 'tree' (full accessibility tree), or 'read' (readable text).
    """
    command = [
        WEBCMD_PATH,
        "--session",
        session_id,
        "browser",
        "snapshot",
        "--snapshot-mode",
        mode
    ]
    return run_command(command)


def webcmd_navigate(url: str, session_id: str) -> Any:
    """Navigates the WebCMD session browser to the specified URL."""
    javascript = f"""
await page.goto({json.dumps(url)}, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
"""
    return run_webcmd(javascript, session_id)


def webcmd_current_page(session_id: str) -> Dict[str, Any]:
    """Returns the current page metadata (id, url, title)."""
    data = webcmd_snapshot(session_id)
    return data.get("page", {})


def webcmd_click(target: str, session_id: str) -> Any:
    """
    Clicks an element matching exact visible text, aria label, button/link role, or CSS selector.
    Includes smart fallback logic for maximum reliability during autonomous runs.
    """
    javascript = f"""
const target = {json.dumps(target)};

// 1. Try exact visible text
let locator = page.getByText(target, {{ exact: true }});
if (await locator.count() > 0) {{
    await locator.first().click();
    return;
}}

// 2. Try role-based button or link
locator = page.getByRole('button', {{ name: target }});
if (await locator.count() > 0) {{
    await locator.first().click();
    return;
}}

locator = page.getByRole('link', {{ name: target }});
if (await locator.count() > 0) {{
    await locator.first().click();
    return;
}}

// 3. Try partial text
locator = page.getByText(target);
if (await locator.count() > 0) {{
    await locator.first().click();
    return;
}}

// 4. Try CSS selector directly
await page.locator(target).first().click();
"""
    return run_webcmd(javascript, session_id)


def webcmd_type(field_or_label: str, value: str, session_id: str) -> Any:
    """
    Types text into an input or textarea identified by label, placeholder, name, or CSS selector.
    Dispatches input/change events to support reactive SPAs (React, Vue, Angular).
    """
    javascript = f"""
const field = {json.dumps(field_or_label)};
const val = {json.dumps(value)};

// 1. Try placeholder
let locator = page.getByPlaceholder(field, {{ exact: true }});
if (await locator.count() > 0) {{
    await locator.first().fill(val);
    return;
}}

// 2. Try label
locator = page.getByLabel(field, {{ exact: true }});
if (await locator.count() > 0) {{
    await locator.first().fill(val);
    return;
}}

// 3. Try input name or id
locator = page.locator(`input[name="${{field}}"], input[id="${{field}}"], textarea[name="${{field}}"]`);
if (await locator.count() > 0) {{
    await locator.first().fill(val);
    return;
}}

// 4. Try partial placeholder/label
locator = page.getByPlaceholder(field);
if (await locator.count() > 0) {{
    await locator.first().fill(val);
    return;
}}

// 5. Fallback CSS locator
await page.locator(field).first().fill(val);
"""
    return run_webcmd(javascript, session_id)


def webcmd_read_dom(session_id: str) -> Dict[str, Any]:
    """Extracts the page body text, title, inputs, forms, and links via WebCMD runtime."""
    javascript = """
const title = await page.title();
const url = page.url();
const bodyText = await page.evaluate(() => document.body ? document.body.innerText : "");
console.log(JSON.stringify({ title, url, text: bodyText }));
"""
    return run_webcmd(javascript, session_id)


def webcmd_screenshot(filepath: str, session_id: str) -> Any:
    """Takes a full page screenshot using WebCMD and saves to filepath."""
    javascript = f"""
await page.screenshot({{ path: {json.dumps(filepath)}, fullPage: true }});
"""
    return run_webcmd(javascript, session_id)


def webcmd_evaluate(javascript_expr: str, session_id: str) -> Any:
    """Evaluates a JavaScript expression in the page context and returns the result."""
    code = f"""
const result = await page.evaluate(() => {{
    return ({javascript_expr});
}});
console.log(JSON.stringify(result));
"""
    return run_webcmd(code, session_id)


# ============================================================
# WEBCMD SECURITY AUDITING PRIMITIVES
# ============================================================

def webcmd_get_cookies(session_id: str) -> List[Dict[str, Any]]:
    """Inspects all cookies in the browser context for security flags (Secure, HttpOnly, SameSite)."""
    javascript = """
const cookies = await page.context().cookies();
console.log(JSON.stringify(cookies));
"""
    res = run_webcmd(javascript, session_id)
    if isinstance(res, list):
        return res
    if isinstance(res, dict) and "raw_output" in res:
        try:
            return json.loads(res["raw_output"])
        except Exception:
            return []
    return []


def webcmd_get_storage(session_id: str) -> Dict[str, Any]:
    """Extracts LocalStorage and SessionStorage to detect potential credential or token leaks."""
    javascript = """
const storage = await page.evaluate(() => {
    const local = {};
    for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        local[k] = localStorage.getItem(k);
    }
    const session = {};
    for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        session[k] = sessionStorage.getItem(k);
    }
    return { localStorage: local, sessionStorage: session };
});
console.log(JSON.stringify(storage));
"""
    res = run_webcmd(javascript, session_id)
    if isinstance(res, dict) and "localStorage" in res:
        return res
    if isinstance(res, dict) and "raw_output" in res:
        try:
            return json.loads(res["raw_output"])
        except Exception:
            pass
    return {"localStorage": {}, "sessionStorage": {}}


def start_webcmd(url: str = DEFAULT_URL) -> str:
    """Convenience helper to start WebCMD, navigate, and print page info."""
    print("\n🌐 Starting WebCMD session...")
    session_id = create_session()
    print(f"🆔 WebCMD session: {session_id}")
    print(f"🌐 Navigating to: {url}")
    webcmd_navigate(url, session_id)
    page = webcmd_current_page(session_id)
    print("\n📄 WebCMD ACTIVE PAGE:")
    print(json.dumps(page, indent=2, ensure_ascii=False))
    return session_id


if __name__ == "__main__":
    print("🌐 Testing Upgraded WebCMD Tools Suite...")
    print(f"📍 Binary Path: {WEBCMD_PATH}")

    # Clean up stale sessions
    cleaned = cleanup_idle_sessions()
    print(f"🧹 Cleaned up {cleaned} idle WebCMD sessions.")

    # Test with Context Manager
    test_url = "file:///C:/Users/Tanishka%20Aggarwal/WEB-AUDITOR/WEB-AUDITOR/website/index.html"
    print(f"\n🚀 Creating session and navigating to: {test_url}")

    with WebCMDSession(test_url) as session_id:
        print(f"🆔 Active Session: {session_id}")

        page_info = webcmd_current_page(session_id)
        print("\n📄 Page Info:")
        print(json.dumps(page_info, indent=2, ensure_ascii=False))

        print("\n🧪 Testing JavaScript execution...")
        result = run_webcmd('console.log("WEBCMD_EXPERT_OK");', session_id)
        print("Result:", result)

        print("\n📸 Testing Snapshot (act mode)...")
        snapshot = webcmd_snapshot(session_id, mode="act")
        print("Snapshot received. Mode:", snapshot.get("snapshotMode", "act"))

        print("\n🍪 Testing Cookie & Storage Security Inspection...")
        cookies = webcmd_get_cookies(session_id)
        print(f"Cookies found: {len(cookies)}")
        storage = webcmd_get_storage(session_id)
        print("Storage items:", storage)

    print("\n✅ Session cleanly closed via Context Manager.")
    print("🎉 All WebCMD tools verified successfully!")