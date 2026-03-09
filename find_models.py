from google import genai
import sys

api_key = "AIzaSyBAfTOG_zioIiPnX4cVcpxWINJ1znxiOUM"
client = genai.Client(api_key=api_key)

try:
    models = client.models.list(config={'page_size': 50})
    print("--- ALL SUPPORTED MODELS ---")
    for m in models:
        # Check if generateContent is in the supported methods
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name} [supported]")
        else:
            print(f"- {m.name} [unsupported]")
except Exception as e:
    print(f"FAILED TO LIST: {str(e)}")
