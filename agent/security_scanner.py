import sys
from urllib.parse import urljoin

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ============================================================
# SINGLE PAGE SCANNER (HIGH PERFORMANCE)
# ============================================================

def scan_page(page, response_headers=None):
    """
    Passively inspect the currently loaded page with high performance.
    All DOM metrics, forms, inputs, links, scripts, and storage keys
    are extracted in a single in-browser evaluation round-trip.
    """
    findings = []
    url = page.url
    title = page.title()

    # Single-pass DOM security extraction in browser JavaScript
    try:
        dom_data = page.evaluate("""() => {
            const result = {
                links: [],
                forms: [],
                inputs: [],
                buttonsCount: document.querySelectorAll('button').length,
                scriptsCount: document.querySelectorAll('script').length,
                inlineHandlersCount: 0,
                storageKeys: []
            };

            // Links
            document.querySelectorAll('a').forEach(a => {
                result.links.push({
                    href: a.getAttribute('href') || '',
                    text: (a.innerText || '').trim()
                });
            });

            // Forms
            document.querySelectorAll('form').forEach(f => {
                const hasPassword = f.querySelectorAll('input[type="password"]').length > 0;
                result.forms.push({
                    method: (f.getAttribute('method') || 'GET').toUpperCase(),
                    action: f.getAttribute('action') || '',
                    hasPassword: hasPassword
                });
            });

            // Inputs
            document.querySelectorAll('input, textarea, select').forEach(inp => {
                result.inputs.push({
                    type: (inp.getAttribute('type') || '').toLowerCase(),
                    autocomplete: inp.getAttribute('autocomplete')
                });
            });

            // Inline Event Handlers
            const inlineAttrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onchange', 'onsubmit'];
            let inlineCount = 0;
            document.querySelectorAll('*').forEach(el => {
                for (let attr of inlineAttrs) {
                    if (el.hasAttribute(attr)) {
                        inlineCount++;
                        break;
                    }
                }
            });
            result.inlineHandlersCount = inlineCount;

            // Storage keys
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    result.storageKeys.push({ storage: 'localStorage', key: localStorage.key(i) });
                }
                for (let i = 0; i < sessionStorage.length; i++) {
                    result.storageKeys.push({ storage: 'sessionStorage', key: sessionStorage.key(i) });
                }
            } catch(e) {}

            return result;
        }""")
    except Exception as eval_err:
        dom_data = {
            "links": [],
            "forms": [],
            "inputs": [],
            "buttonsCount": 0,
            "scriptsCount": 0,
            "inlineHandlersCount": 0,
            "storageKeys": []
        }

    # 1. Process Links
    for link in dom_data.get("links", []):
        href = link.get("href", "")
        text = link.get("text", "")
        if not href:
            findings.append({
                "severity": "INFO",
                "type": "LINK",
                "message": f"Link '{text}' has no href."
            })
            continue

        abs_url = urljoin(url, href)
        if (
            abs_url.startswith("http")
            and not abs_url.startswith("http://127.0.0.1")
            and not abs_url.startswith("http://localhost")
        ):
            findings.append({
                "severity": "INFO",
                "type": "EXTERNAL_LINK",
                "message": f"External link detected: {abs_url}"
            })

    # 2. Process Forms
    for form in dom_data.get("forms", []):
        if form.get("hasPassword") and form.get("method") == "GET":
            findings.append({
                "severity": "HIGH",
                "type": "FORM",
                "message": "Password field is present in a GET form."
            })

    # 3. Process Inputs
    for inp in dom_data.get("inputs", []):
        if inp.get("type") == "password":
            findings.append({
                "severity": "INFO",
                "type": "PASSWORD_FIELD",
                "message": "Password input detected."
            })
            if not inp.get("autocomplete"):
                findings.append({
                    "severity": "LOW",
                    "type": "PASSWORD_FIELD",
                    "message": "Password field has no autocomplete attribute."
                })

    # 4. Inline Handlers
    inline_count = dom_data.get("inlineHandlersCount", 0)
    if inline_count > 0:
        findings.append({
            "severity": "LOW",
            "type": "JAVASCRIPT",
            "message": f"{inline_count} inline event handler(s) detected."
        })

    # 5. Security Headers (Check headers directly from navigation response)
    headers = response_headers or {}
    if not headers and not url.startswith("file://"):
        try:
            resp = page.request.get(url, timeout=3000)
            headers = resp.headers
        except Exception:
            pass

    if headers:
        security_headers = {
            "content-security-policy": "Content-Security-Policy",
            "x-frame-options": "X-Frame-Options",
            "x-content-type-options": "X-Content-Type-Options",
            "referrer-policy": "Referrer-Policy"
        }
        for key, display_name in security_headers.items():
            if key not in headers:
                findings.append({
                    "severity": "LOW",
                    "type": "SECURITY_HEADER",
                    "message": f"Missing security header: {display_name}"
                })

    # 6. Storage Leak Audit
    sensitive_keywords = ["token", "auth", "jwt", "password", "secret", "apikey", "api_key", "session", "credential"]
    for item in dom_data.get("storageKeys", []):
        k = (item.get("key") or "").lower()
        store_name = item.get("storage", "Web Storage")
        if any(word in k for word in sensitive_keywords):
            findings.append({
                "severity": "MEDIUM",
                "type": "STORAGE_LEAK",
                "message": f"Sensitive key '{item.get('key')}' detected in unencrypted {store_name}."
            })

    # 7. Cookie Flags Audit
    try:
        cookies = page.context.cookies([url]) if not url.startswith("file://") else []
        for cookie in cookies:
            cookie_name = cookie.get("name", "unknown")
            if not cookie.get("httpOnly"):
                findings.append({
                    "severity": "LOW",
                    "type": "COOKIE_FLAG",
                    "message": f"Cookie '{cookie_name}' lacks HttpOnly flag (vulnerable to XSS extraction)."
                })
            if not cookie.get("secure") and url.startswith("https"):
                findings.append({
                    "severity": "LOW",
                    "type": "COOKIE_FLAG",
                    "message": f"Cookie '{cookie_name}' lacks Secure flag over HTTPS."
                })
            same_site = str(cookie.get("sameSite", "")).lower()
            if same_site in ["none", ""]:
                findings.append({
                    "severity": "LOW",
                    "type": "COOKIE_FLAG",
                    "message": f"Cookie '{cookie_name}' has SameSite={same_site or 'Unset'} (increased CSRF risk)."
                })
    except Exception:
        pass

    return {
        "url": url,
        "title": title,
        "links": len(dom_data.get("links", [])),
        "forms": len(dom_data.get("forms", [])),
        "inputs": len(dom_data.get("inputs", [])),
        "buttons": dom_data.get("buttonsCount", 0),
        "scripts": dom_data.get("scriptsCount", 0),
        "inline_handlers": inline_count,
        "findings": findings
    }


# ============================================================
# COMPLETE WEBSITE SCANNER (HIGH SPEED)
# ============================================================

def scan_website(
    browser,
    base_url,
    pages
):
    """
    Scan multiple pages with high-speed resource routing and domcontentloaded checks.
    """
    page = browser.new_page()

    # Block heavy media and tracking to accelerate scan by 10x
    try:
        page.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,ico,woff,woff2,ttf,eot,mp4,mp3,avi,webm}",
            lambda route: route.abort()
        )
    except Exception:
        pass

    reports = []
    all_findings = []

    for page_name in pages:
        if page_name.startswith(("http://", "https://", "file://")):
            url = page_name
        elif page_name == base_url:
            url = page_name
        else:
            url = base_url.rstrip("/") + "/" + page_name

        print(f"🔍 Fast scanning: {url}")

        try:
            # High speed domcontentloaded navigation with 8s timeout
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=8000
            )

            resp_headers = response.headers if response else {}

            report = scan_page(page, response_headers=resp_headers)
            reports.append(report)

            for finding in report["findings"]:
                finding_copy = finding.copy()
                finding_copy["page"] = url
                all_findings.append(finding_copy)

        except Exception as error:
            print(f"⚠️ Quick scan notice for {page_name}: {error}")

    # Severity Summary
    severity_summary = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "INFO": 0
    }

    for finding in all_findings:
        severity = finding.get("severity", "INFO")
        if severity in severity_summary:
            severity_summary[severity] += 1

    final_report = {
        "base_url": base_url,
        "pages_scanned": len(reports),
        "total_findings": len(all_findings),
        "severity_summary": severity_summary,
        "reports": reports,
        "findings": all_findings
    }

    try:
        page.close()
    except Exception:
        pass

    return final_report