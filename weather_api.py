import requests

API_KEY = "1619e742903443d5400c8343c452ecba"  #  OpenWeatherMap API key

def get_user_location():
    """
    Get user's current city and location coordinates (lat, lon) using ipinfo.io service.
    Returns (city, (lat, lon)) or (None, None) if failed.
    """
    try:
        response = requests.get('https://ipinfo.io/')
        data = response.json()
        city = data.get('city', None)
        loc = data.get('loc', None)  # format "latitude,longitude"
        if loc:
            lat, lon = loc.split(',')
            return city, (float(lat), float(lon))
        return city, (None, None)
    except Exception:
        return None, (None, None)

def get_weather(city):
    """
    Get current weather by city name using OpenWeatherMap API.
    """
    api_key = API_KEY
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("cod") != 200:
            return f"Could not find weather for '{city}'."
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        return f"Weather in {city.title()}: {weather}, {temp}°C"
    except Exception:
        return "Sorry, I couldn't fetch the weather right now."

def get_weather_by_coordinates(lat, lon):
    """
    Get current weather by latitude and longitude using OpenWeatherMap API.
    """
    api_key = API_KEY
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("cod") != 200:
            return f"Could not find weather for the location."
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        return f"Current Weather: {weather}, {temp}°C"
    except Exception:
        return "Sorry, I couldn't fetch the weather right now."

def get_7_day_forecast(lat, lon):
    """
    Get 7-day weather forecast for coordinates using OpenWeatherMap One Call API.
    Returns a formatted string with daily weather.
    """
    api_key = API_KEY
    url = f"http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "daily" not in data:
            return "Could not retrieve forecast data."
        from datetime import datetime
        daily_forecasts = data["daily"]
        forecast_data = []
        for day in daily_forecasts[:7]:  # 7 days forecast including today
            date = datetime.fromtimestamp(day["dt"]).strftime("%A, %b %d")
            weather = day["weather"][0]["description"].capitalize()
            temp_day = day["temp"]["day"]
            temp_night = day["temp"]["night"]
            forecast_data.append(f"{date}: {weather}, Day {temp_day}°C / Night {temp_night}°C")
        return "\n".join(forecast_data)
    except Exception:
        return "Sorry, I couldn't fetch the forecast data right now."
