import os
import sys
from urllib.parse import urljoin, urlparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

START_URL = os.getenv(
    "WEB_AUDITOR_URL",
    "http://127.0.0.1:5500/website/index.html"
)


def explore_website(page, start_url=None, max_pages=15):
    """
    High-speed page discovery.
    Extracts all page links in a single JavaScript evaluate call,
    blocks heavy assets, and enforces sensible crawl limits.
    """
    initial_url = start_url or START_URL
    visited = set()
    to_visit = [initial_url]

    parsed_start = urlparse(initial_url)
    start_domain = parsed_start.netloc

    # Block heavy media for 10x faster crawling
    try:
        page.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,ico,woff,woff2,ttf,eot,mp4,mp3}",
            lambda route: route.abort()
        )
    except Exception:
        pass

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop()

        if current_url in visited:
            continue

        print(f"🔎 Exploring: {current_url}")

        try:
            page.goto(
                current_url,
                wait_until="domcontentloaded",
                timeout=6000
            )

            visited.add(current_url)

            # Extract all links in a single in-browser JavaScript call
            extracted_links = page.evaluate("""() => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                        links.push(href);
                    }
                });
                return links;
            }""")

            for href in extracted_links:
                full_url = urljoin(current_url, href).split("#")[0].split("?")[0]
                parsed = urlparse(full_url)

                # Same domain or same local path
                if (start_domain and parsed.netloc == start_domain) or (not start_domain and not parsed.netloc):
                    if full_url not in visited and full_url not in to_visit and len(visited) + len(to_visit) < max_pages:
                        to_visit.append(full_url)

        except Exception as error:
            print(f"⚠️ Exploration note for {current_url}: {error}")
            visited.add(current_url)

    print(f"✅ Fast exploration complete. Discovered {len(visited)} pages.")
    return list(visited)