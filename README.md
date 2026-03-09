<div align="center">

# ⚡ Because Market — Ops Copilot

**An AI-powered internal operations assistant that transforms messy tickets, customer complaints, and internal requests into structured, actionable plans — in seconds.**

Built with **Flask** + **Google Gemini** (Multi-Model Fallback) | Designed for the Because Market ops team

**[🚀 Live Demo — Deployed on Railway](https://op-assistant-production.up.railway.app)**

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0+-black?style=flat-square&logo=flask)
![Gemini](https://img.shields.io/badge/Google_Gemini-Robust_Fallback-orange?style=flat-square&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 📸 UI Walkthrough

### 🔍 AI Analysis Results
The Copilot takes any messy text and instantly generates a structured summary, priority level, estimated time, and actionable steps.

<p align="center">
  <img src="screenshots/full_response.png" alt="Full Analysis Result" width="800"/>
</p>

---

### 📋 Request History
Never lose an analysis. The last 20 requests are saved locally for instant recall, complete with priority badges and timestamps.

<p align="center">
  <img src="screenshots/history.png" alt="Request History" width="800"/>
</p>

---

### 🌙 Dark Mode & Premium UI
Full dark mode support with a clean, modern aesthetic designed for productivity.

<p align="center">
  <img src="screenshots/dark_mode.png" alt="Dark Mode" width="800"/>
</p>

---

## 🚀 Key Features

| Feature | Details |
|---|---|
| 🤖 **Multi-Model Fallback** | Automatically swaps between **Gemini 2.5 Flash**, **2.0 Flash Lite**, and **1.5 Flash** to bypass quota limits and availability issues. |
| 🔄 **Exponential Retries** | Uses `tenacity` to automatically retry failed requests with backoff — ensuring a smooth experience during traffic spikes. |
| 🔑 **Bring Your Own Key** | Deployed instances allow users to enter their own Gemini API key in Settings, which is securely stored in `localStorage`. |
| ✅ **Instant Key Validation** | Validates API keys in real-time within the Settings panel before saving. |
| 📝 **Smart Triage** | Categorizes requests by Priority (High/Medium/Low) and assigns them to the correct department (Logistics, Marketing, CS, etc.). |
| ⚡ **Response Caching** | In-memory backend caching prevents redundant API calls for identical requests. |

---

## 🏗️ Architecture & Logic

The Ops Copilot is designed to be **unbreakable** in production:

1.  **Request**: User enters data → Frontend checks `localStorage` for their private API key.
2.  **Validation**: App ensures input isn't empty (with UI feedback) and checks the cache.
3.  **Haiku Strategy**:
    - **Attempt 1**: `gemini-2.0-flash-lite` (Fastest/Cheapest)
    - **Fallback 1**: `gemini-1.5-flash` (Stable bucket)
    - **Fallback 2**: `gemini-1.5-flash-8b` (Emergency quota)
4.  **Formatting**: Model returns raw JSON which is parsed and rendered with staggered fade-in animations.

---

## 🛠️ Local Setup

### 1. Clone & Environment
```bash
git clone git@github.com:krtanay/Op-Assistant.git
cd Op-Assistant
python -m venv .venv
# Windows: .venv\Scripts\activate | Mac: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file or use the **Settings** tab in the browser once the app is running:
```bash
GEMINI_API_KEY=your_key_here
```
> Get a free key at [Google AI Studio](https://aistudio.google.com/).

### 3. Launch
```bash
python app.py
```
Visit `http://127.0.0.1:5000` ⚡

---

## 🌐 Production Deployment (Railway)

This app is optimized for platforms like **Railway** or **Render**:
1.  **Procfile**: Included for Gunicorn production service.
2.  **Port Binding**: Automatically binds to `$PORT`.
3.  **Security**: No sensitive keys are committed; the app gracefully prompts the user to input their own key if the server doesn't have one.

---

## 🧩 Tech Stack

- **Backend**: Python 3.11+, Flask 3.x, Gunicorn, Tenacity
- **AI**: Google Gemini SDK (`google-genai`)
- **Frontend**: Vanilla HTML5, CSS3 (Modern HSL system), JavaScript (ES6+)
- **Storage**: Browser Persistence (localStorage)

---

<div align="center">
  Built with ❤️ for Because Market by <a href="https://github.com/krtanay">@krtanay</a>
</div>
