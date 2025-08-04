import google.generativeai as genai
import os

GEMINI_API_KEY = ""


try:
    print("Configuring the Gemini client...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-pro')

    print("Sending a simple prompt to gemini...")
    response = model.generate_content("Hello, world! In one sentence, who are you?")

    print("\n--- Gemini's Response ---")
    print(response.text)
    print("------------------------")
    print("\nTest successful!")


except Exception as e:
    print(f"\nAn error occurred: {e}")