from google import genai
from google.genai import types

api_key = "AIzaSyBAfTOG_zioIiPnX4cVcpxWINJ1znxiOUM"
client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-1.5-flash"
]

print("--- AUDIT ---")
for m in models_to_test:
    try:
        # Don't force version, let the SDK handle it
        client.models.generate_content(
            model=m,
            contents="say hi",
            config=types.GenerateContentConfig(max_output_tokens=1)
        )
        print(f"SUCCESS: {m}")
    except Exception as e:
        print(f"FAILED: {m} - {str(e)}")
