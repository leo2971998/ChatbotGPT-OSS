# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, re, requests

# === Config ==================================================================
# Point to your local Ollama's OpenAI-compatible Chat Completions endpoint.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
MODEL = os.getenv("MODEL", "gpt-oss:20b")
ENABLE_WEATHER = os.getenv("ENABLE_WEATHER", "1") == "1"   # set to "0" to disable

# Units note: Open-Meteo defaults to °C and km/h for these fields.

# === App =====================================================================
app = Flask(__name__)
CORS(app)  # for local dev; restrict in production

# === Helpers =================================================================
def safe_round(x):
    try:
        return round(float(x))
    except Exception:
        return None

def as_deg(x):
    v = safe_round(x)
    return f"{v}°" if v is not None else "—"

def as_pct(x):
    v = safe_round(x)
    return f"{v}%" if v is not None else "—"

def as_speed(x):
    v = safe_round(x)
    return f"{v} km/h" if v is not None else "—"

def find_weather_city(text: str):
    """
    Extract a probable city name from prompts like:
      - 'weather in Austin'
      - 'what's the weather at Paris, FR?'
    """
    m = re.search(r"\bweather\b.*?\b(?:in|at|for)\b\s+([A-Za-z .,'-]+)", text, flags=re.I)
    return m.group(1).strip() if m else None

def get_weather_card(city: str):
    """Fetch weather data from Open-Meteo and format a UI card payload."""
    # 1) geocode
    g = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    g.raise_for_status()
    results = g.json().get("results") or []
    if not results:
        return None

    lat = results[0]["latitude"]
    lon = results[0]["longitude"]
    resolved = f'{results[0]["name"]}, {results[0].get("admin1", "") or results[0].get("country_code", "")}'.strip(", ")

    # 2) current + daily forecast
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,uv_index_max",
            "timezone": "auto",
        },
        timeout=10,
    )
    w.raise_for_status()
    data = w.json()
    cur = data.get("current", {}) or {}
    daily = data.get("daily", {}) or {}

    code = int(cur.get("weather_code", 0))
    label = WEATHER_CODES.get(code, "Unknown")

    return {
        "type": "weather",
        "location": resolved,
        "temperature": cur.get("temperature_2m"),
        "feelsLike": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"),
        "wind": cur.get("wind_speed_10m"),
        "condition": label,
        "icon": WEATHER_ICONS.get(code, "🌡️"),
        "high": (daily.get("temperature_2m_max") or [None])[0],
        "low": (daily.get("temperature_2m_min") or [None])[0],
        "uv": (daily.get("uv_index_max") or [None])[0],
    }

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}
WEATHER_ICONS = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    61: "🌦️", 63: "🌧️", 65: "🌧️",
    71: "🌨️", 73: "❄️", 75: "❄️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}

def call_llm(text: str) -> str:
    """Send a chat request to Ollama's OpenAI-compatible endpoint."""
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. When using math, format with LaTeX: "
                    "inline as $...$ and display as $$...$$. Do not emit HTML."
                ),
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0.7,
    }
    r = requests.post(
        OLLAMA_URL,
        headers={"Authorization": "Bearer ollama", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

# === Routes ==================================================================
@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("message") or "").strip()
    if not text:
        return jsonify({"error": "Message is required"}), 400

    # 1) Weather card path (optional)
    if ENABLE_WEATHER:
        city = find_weather_city(text)
        if city:
            try:
                card = get_weather_card(city)
                if not card:
                    return jsonify({"reply": f"Sorry, I couldn't find weather for '{city}'."})
                reply = (
                    f"{card['icon']} {card['location']}: {card['condition']}. "
                    f"{as_deg(card['temperature'])} feels {as_deg(card['feelsLike'])}. "
                    f"H:{as_deg(card['high'])} / L:{as_deg(card['low'])}  •  "
                    f"Humidity {as_pct(card['humidity'])}  •  Wind {as_speed(card['wind'])}."
                )
                return jsonify({"reply": reply, "ui": card})
            except Exception as exc:
                return jsonify({"error": f"Weather lookup failed: {exc}"}), 500

    # 2) Normal LLM path
    try:
        reply = call_llm(text)
        return jsonify({"reply": reply})
    except Exception as exc:
        # Log server-side as needed: app.logger.exception(exc)
        return jsonify({"error": str(exc)}), 500

@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL, "ollama_url": OLLAMA_URL})

# === Main ====================================================================
if __name__ == "__main__":
    # Bind to loopback only for safety in local dev
    app.run(host="127.0.0.1", port=5000, debug=True)
