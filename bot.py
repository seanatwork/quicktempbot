import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


def get_temperature(query: str) -> str:
    # Geocode using Nominatim (OpenStreetMap) — handles ZIP codes, cities, "city, state", etc.
    geo_url = "https://nominatim.openstreetmap.org/search"
    
    # If it's a 5-digit ZIP code, prefer US results
    search_query = query
    if query.isdigit() and len(query) == 5:
        search_query = f"{query}, USA"
    
    geo_resp = requests.get(
        geo_url,
        params={"q": search_query, "format": "json", "limit": 1, "addressdetails": 1},
        headers={"User-Agent": "quicktempbot/1.0"},
        timeout=10,
    )
    geo_data = geo_resp.json()

    if not geo_data:
        return f'Could not find location: "{query}"'

    loc = geo_data[0]
    lat, lon = loc["lat"], loc["lon"]
    label = loc.get("display_name", query)

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
