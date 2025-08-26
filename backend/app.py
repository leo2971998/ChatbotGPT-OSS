from flask import Flask, request, jsonify
from flask_cors import CORS
import os, re, requests

# Optional: adjust these if running Ollama elsewhere
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "gpt-oss:20b"

app = Flask(__name__)
CORS(app)


# --- Helpers -----------------------------------------------------------------
def find_weather_city(text: str) -> str | None:
    """Extract a city name from prompts like 'weather in Austin'."""
    match = re.search(r"\bweather\b.*?\b(?:in|at|for)\b\s+([A-Za-z .,'-]+)", text, flags=re.I)
    if match:
        return match.group(1).strip()
    return None


def get_weather_card(city: str):
    """Fetch weather data from Open-Meteo and format a UI card payload."""
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo.raise_for_status()
    results = geo.json().get("results") or []
    if not results:
        return None
    lat = results[0]["latitude"]
    lon = results[0]["longitude"]
    resolved = f"{results[0]['name']}, {results[0].get('admin1', '') or results[0].get('country_code', '')}".strip(", ")

    weather = requests.get(
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
    weather.raise_for_status()
    data = weather.json()
    current = data.get("current", {})
    daily = data.get("daily", {})

    code = int(current.get("weather_code", 0))
    label = WEATHER_CODES.get(code, "Unknown")
    return {
        "type": "weather",
        "location": resolved,
        "temperature": current.get("temperature_2m"),
        "feelsLike": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind": current.get("wind_speed_10m"),
        "condition": label,
        "icon": WEATHER_ICONS.get(code, "🌡️"),
        "high": (daily.get("temperature_2m_max") or [None])[0],
        "low": (daily.get("temperature_2m_min") or [None])[0],
        "uv": (daily.get("uv_index_max") or [None])[0],
    }


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Heavy showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ hail",
    99: "Thunderstorm w/ heavy hail",
}


WEATHER_ICONS = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    61: "🌦️",
    63: "🌧️",
    65: "🌧️",
    71: "🌨️",
    73: "❄️",
    75: "❄️",
    80: "🌦️",
    81: "🌧️",
    82: "⛈️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}


# --- Routes ------------------------------------------------------------------
@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("message") or "").strip()
    if not text:
        return jsonify({"error": "Message is required"}), 400

    city = find_weather_city(text)
    if city:
        try:
            card = get_weather_card(city)
            if not card:
                return jsonify({"reply": f"Sorry, I couldn't find weather for '{city}'."})
            reply = (
                f"{card['icon']} {card['location']}: {card['condition']}. "
                f"{round(card['temperature'])}°C feels {round(card['feelsLike'])}°C. "
                f"H:{round(card['high'])}° / L:{round(card['low'])}°  •  "
                f"Humidity {round(card['humidity'])}%  •  Wind {round(card['wind'])} km/h."
            )
            return jsonify({"reply": reply, "ui": card})
        except Exception as exc:
            return jsonify({"error": f"Weather lookup failed: {exc}"}), 500

    try:
        resp = requests.post(
            OLLAMA_URL,
            headers={"Authorization": "Bearer ollama", "Content-Type": "application/json"},
            json={
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
            },
            timeout=60,
        )
        resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

