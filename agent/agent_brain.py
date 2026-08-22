from playwright.sync_api import sync_playwright
from google import genai
from dotenv import load_dotenv
import os


# --------------------------------------------------
# 1. LOAD GEMINI API KEY
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Gemini API key nahi mili.")
    exit()

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# 2. WEBSITE WE WANT TO EXPLORE
# --------------------------------------------------

START_URL = "http://127.0.0.1:5500/website/"

# --------------------------------------------------
# 3. EXPLORE WEBSITE
# --------------------------------------------------

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto(START_URL)

    print("\n🌐 Website opened.")

    # Get visible text
    page_text = page.locator("body").inner_text()

    # Get links
    links = page.locator("a")

    link_information = []

    for i in range(links.count()):

        link = links.nth(i)

        text = link.inner_text()

        href = link.get_attribute("href")

        link_information.append(
            f"{text} → {href}"
        )


    # --------------------------------------------------
    # 4. CREATE INFORMATION FOR GEMINI
    # --------------------------------------------------

    website_information = f"""

WEBSITE URL:
{START_URL}

PAGE TITLE:
{page.title()}

VISIBLE CONTENT:
{page_text}

LINKS:
{chr(10).join(link_information)}

"""


    print("\n📄 Information collected from website.")
    print(website_information)


    # --------------------------------------------------
    # 5. ASK GEMINI TO UNDERSTAND THE WEBSITE
    # --------------------------------------------------

    prompt = f"""

You are an intelligent browser-agent planner.

You have been given information from a website.

Your job is to understand what a normal user
could do on this website.

Identify the important user workflows that
should be tested.

For each workflow provide:

1. Workflow name
2. Starting page
3. Actions the user would perform
4. Expected result

Do NOT invent features that are not supported
by the website.

Here is the website information:

{website_information}

"""


    print("\n🧠 Asking Gemini to understand the website...")


    response = client.models.generate_content(

        model="gemini-3.6-flash",

        contents=prompt

    )


    # --------------------------------------------------
    # 6. DISPLAY AI'S UNDERSTANDING
    # --------------------------------------------------

    print("\n")
    print("=" * 60)

    print("🤖 GEMINI'S WEBSITE ANALYSIS")

    print("=" * 60)

    print(response.text)

    print("=" * 60)


    browser.close()