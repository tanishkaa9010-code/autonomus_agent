from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Gemini API key nahi mili.")
    exit()

print("✅ Gemini API key loaded successfully.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="""
You are the reasoning engine of a website auditing agent.

A website contains:
- Home
- Login
- Sign Up
- Products
- Add to Cart

Identify the main user workflows that should be tested.

Give a short numbered list.
"""
)

print("\n🤖 GEMINI RESPONSE:\n")
print(response.text)