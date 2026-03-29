import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


def get_temperature(query: str) -> str:
    # Geocode the location (city, state, ZIP, etc.)
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_resp = requests.get(geo_url, params={"name": query, "count": 1}, timeout=10)
    geo_data = geo_resp.json()

    results = geo_data.get("results")
    if not results:
        return f'Could not find location: "{query}"'

    loc = results[0]
    lat, lon = loc["latitude"], loc["longitude"]
    name = loc.get("name", query)
    country = loc.get("country", "")
    admin1 = loc.get("admin1", "")
    label = ", ".join(filter(None, [name, admin1, country]))

    # Fetch current temperature
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_resp = requests.get(
        weather_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "temperature_unit": "fahrenheit",
        },
        timeout=10,
    )
    weather_data = weather_resp.json()
    temp_f = weather_data["current_weather"]["temperature"]
    temp_c = round((temp_f - 32) * 5 / 9, 1)

    return f"{label}\nCurrent temperature: {temp_f}°F / {temp_c}°C"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    reply = get_temperature(query)
    await update.message.reply_text(reply)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()
