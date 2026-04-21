from flask import Flask, render_template
from datetime import datetime as dt
import json
import requests


app = Flask(__name__)


def get_live_weather_data():
    """Fetch live weather data from the WeatherAPI forecast endpoint."""
    api_key = ""
    url = "http://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": api_key,
        "q": "London",
        "days": 3,
    }

    response = requests.get(url, params=params)
    return response.json()

data = get_live_weather_data()

# Current weather data
weather_datetime_str = data["location"]["localtime"]
dt_obj = dt.strptime(weather_datetime_str, "%Y-%m-%d %H:%M")

current_day = dt.strftime(dt_obj, "%B %d")
current_time = dt.strftime(dt_obj, "%H:%M")

current_temp = round(int(data["current"]["temp_c"]))
feels_like_c = round(int(data["current"]["feelslike_c"]))
weather_condition = data["current"]["condition"]["text"]
weather_condition_image = data["current"]["condition"]["icon"]

today_forecast = data["forecast"]["forecastday"][0]
today_day_data = today_forecast["day"]
current_data = data["current"]

daily_chance_of_rain = today_day_data["daily_chance_of_rain"]
average_humidity = today_day_data["avghumidity"]

wind_direction = current_data["wind_dir"]
wind_speed = current_data["wind_mph"]

current_sunrise = today_forecast["astro"]["sunrise"]
current_sunset = today_forecast["astro"]["sunset"]


# 3-day forecast
days = []

for forecast_day in data["forecast"]["forecastday"]:
    forecast_dt = dt.strptime(forecast_day["date"], "%Y-%m-%d")
    forecast_day_name = dt.strftime(forecast_dt, "%A")

    day_data = {
        "day": forecast_day_name,
        "high_temp": round(int(forecast_day["day"]["maxtemp_c"])),
        "low_temp": round(int(forecast_day["day"]["mintemp_c"])),
        "chance_of_rain": forecast_day["day"]["daily_chance_of_rain"],
        "image": forecast_day["day"]["condition"]["icon"],
    }

    days.append(day_data)


# Next 5 hourly entries
current_hour = int(dt.strftime(dt_obj, "%H"))
day_index = 0
hours = []

for _ in range(5):
    hourly_data = data["forecast"]["forecastday"][day_index]["hour"][current_hour]

    hour_data = {
        "hour": current_hour,
        "rain_chance": hourly_data["chance_of_rain"],
        "image": hourly_data["condition"]["icon"],
    }

    hours.append(hour_data)

    current_hour += 1

    if current_hour == 24:
        day_index += 1
        current_hour = 0


def check_wind():
    """Return a simple natural-language wind description."""
    current_wind_speed = int(current_data["wind_mph"])

    if current_wind_speed < 2:
        return ""
    if current_wind_speed <= 5:
        return "light winds"
    if current_wind_speed <= 18:
        return "breezy conditions"
    return "windy conditions"


def check_rain():
    """Return a simple natural-language rain description."""
    rain_now = float(current_data["precip_mm"])
    rain_expected = float(today_day_data["totalprecip_mm"])

    if rain_now > 0:
        if rain_expected < 1:
            return "drizzle"
        if rain_expected <= 5:
            return "light rain"
        if rain_expected <= 15:
            return "moderate rain"
        return "heavy rain"

    return ""


def check_condition():
    """Return a natural-language description of the current condition."""
    condition = current_data["condition"]["text"].lower()

    if condition == "clear":
        return "clear at the moment"
    if condition == "sunny":
        return "sunny at the moment"
    if condition == "cloudy":
        return "cloudy right now"
    if condition == "overcast":
        return "overcast currently"

    return f"{condition} at the moment"


def build_summary():
    """Build a short smart summary using condition, rain, and wind."""
    condition_message = check_condition()
    rain_message = check_rain()
    wind_message = check_wind()

    extras = []

    if rain_message:
        extras.append(rain_message)

    if wind_message:
        extras.append(wind_message)

    if len(extras) == 0:
        return condition_message
    if len(extras) == 1:
        return f"{condition_message} with {extras[0]}"

    return f"{condition_message} with {extras[0]} and {extras[1]}"


smart_summary = build_summary().capitalize()


@app.route("/")
def home():
    return render_template(
        "home_page.html",
        current_day=current_day,
        current_time=current_time,
        current_temp=current_temp,
        feelslike_c=feels_like_c,
        weather_condition=weather_condition,
        weather_condition_image=weather_condition_image,
        daily_chance_of_rain=daily_chance_of_rain,
        avghumidity=average_humidity,
        wind_direction=wind_direction,
        wind_speed=wind_speed,
        days=days,
        hours=hours,
        current_sunrise=current_sunrise,
        current_sunset=current_sunset,
        smart_summary=smart_summary,
    )


if __name__ == "__main__":
    app.run(debug=True)