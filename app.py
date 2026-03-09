import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

app = Flask(__name__)

SYSTEM_INSTRUCTION = """You are an operations assistant for Because Market, a fast-growing e-commerce 
startup selling health and wellness products for older adults.

When given a messy internal request, customer complaint, or support ticket, 
return ONLY a valid JSON object in this exact format:

{
  "priority": "High" or "Medium" or "Low",
  "summary": "One clear sentence describing the issue",
  "action_steps": ["Step 1", "Step 2", "Step 3"],
  "estimated_time": "e.g. 30 minutes or 2 hours",
  "department": "e.g. Customer Support, Logistics, Marketing"
}

Rules:
- High = customer-facing issue, refund, urgent complaint
- Medium = internal task, team coordination  
- Low = non-urgent suggestion or improvement
- Return ONLY the JSON. No explanation, no markdown, no extra text."""

FEW_SHOT_EXAMPLES = [
    types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="customer called very upset wrong product arrived needs refund maybe idk urgent help"
        )],
    ),
    types.Content(
        role="model",
        parts=[types.Part.from_text(text="""{
  "priority": "High",
  "summary": "Customer received the wrong product and requires a refund.",
  "action_steps": ["Verify the order details.", "Issue a refund.", "Apologize to the customer."],
  "estimated_time": "30 minutes",
  "department": "Customer Support"
}""")],
    ),
]

GENERATE_CONFIG = types.GenerateContentConfig(
    temperature=0.5,
    top_p=0.8,
    max_output_tokens=150,
    response_mime_type="application/json",
    system_instruction=[
        types.Part.from_text(text=SYSTEM_INSTRUCTION)
    ],
)

response_cache = {}


# Fallback-aware generation: Tries 2.0 Flash Lite, then 1.5 Flash if 429 occurs
def call_gemini_with_fallback(client, contents, config):
    try:
        # Strategy A: Newest/Fastest/Cheapest
        return client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=contents,
            config=config,
        )
    except Exception as e:
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            # Strategy B: Fallback to stable 1.5 Flash (often separate quota)
            return client.models.generate_content(
                model="gemini-1.5-flash",
                contents=contents,
                config=config,
            )
        raise e

# Retry logic: Exponential backoff for transient failures
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def generate_with_retry(client, contents, config):
    return call_gemini_with_fallback(client, contents, config)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    body = request.get_json(silent=True) or {}
    user_input = body.get("text", "").strip()
    user_api_key = body.get("api_key", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Cache check early (saves tokens for repeated inputs)
    if user_input in response_cache:
        return jsonify(response_cache[user_input])

    # Determine which API key to use
    is_custom_key = bool(user_api_key)
    env_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    # Check if we have any key at all
    api_key_to_use = user_api_key or env_api_key

    if not api_key_to_use or "your_gemini_api_key" in api_key_to_use:
        return jsonify({
            "error": "No valid API key configured. Please go to Settings and enter your own Gemini API key."
        }), 401

    try:
        request_client = genai.Client(api_key=api_key_to_use)
        
        # Build conversation: few-shot examples + actual user input
        contents = FEW_SHOT_EXAMPLES + [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)],
            )
        ]

        # Call with retry + fallback
        response = generate_with_retry(request_client, contents, GENERATE_CONFIG)
        full_response = response.text

        # Strip markdown code fences if model wraps response
        clean = full_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]
            clean = clean.rsplit("```", 1)[0]

        result = json.loads(clean.strip())

        # Cache the result
        response_cache[user_input] = result

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Model returned invalid JSON. Try again."}), 500
    except Exception as e:
        err_msg = str(e)
        key_type = "Custom API Key (from Settings)" if is_custom_key else "Server Default Key"
        
        if "API_KEY_INVALID" in err_msg or "401" in err_msg:
            return jsonify({"error": f"Invalid {key_type}. Please check your Settings."}), 401
        
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            return jsonify({
                "error": f"Quota Exceeded for {key_type}. Please wait a minute or use a different key."
            }), 429
            
        return jsonify({"error": f"{key_type} error: {err_msg}"}), 500


@app.route("/test_api", methods=["POST"])
def test_api():
    body = request.get_json(silent=True) or {}
    api_key = body.get("api_key", "").strip()
    
    if not api_key:
        return jsonify({"error": "No API key provided"}), 400
        
    try:
        test_client = genai.Client(api_key=api_key)
        # Simply list models is enough to check key validity, but let's test a generation
        test_client.models.generate_content(
            model="gemini-1.5-flash",
            contents="test",
            config={"max_output_tokens": 1}
        )
        return jsonify({"success": True, "message": "API Key is valid and working!"})
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg:
            return jsonify({"error": "Invalid API Key format or key not found."}), 401
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            return jsonify({"error": "This API Key has exceeded its quota (429)."}), 429
        return jsonify({"error": f"Connection failed: {err_msg}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
