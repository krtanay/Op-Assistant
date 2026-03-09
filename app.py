import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

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

    # Use user-provided API key or fall back to environment variable
    request_client = None
    if user_api_key:
        try:
            request_client = genai.Client(api_key=user_api_key)
        except Exception as e:
            return jsonify({"error": f"Invalid API Key format: {str(e)}"}), 400
    else:
        # Re-initialize from environment variable to ensure updates are picked up
        load_dotenv(override=True)
        request_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    if user_input in response_cache:
        return jsonify(response_cache[user_input])

    # Build conversation: few-shot examples + actual user input
    contents = FEW_SHOT_EXAMPLES + [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)],
        )
    ]

    try:
        # Non-streaming request
        response = request_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=contents,
            config=GENERATE_CONFIG,
        )
        full_response = response.text

        # Strip markdown code fences if model wraps response (e.g. ```json ... ```)
        clean = full_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]  # remove opening fence line
            clean = clean.rsplit("```", 1)[0]  # remove closing fence
        
        result = json.loads(clean.strip())
        
        # Cache the result
        response_cache[user_input] = result
        
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Model returned invalid JSON. Try again."}), 500
    except Exception as e:
        # Check for authentication errors specifically if possible
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "401" in err_msg:
            return jsonify({"error": "Invalid API Key. Please check your settings."}), 401
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            return jsonify({"error": "API Quota exceeded. Please wait a minute or upgrade your plan."}), 429
        return jsonify({"error": err_msg}), 500


if __name__ == "__main__":
    app.run(debug=True)
