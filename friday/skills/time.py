# tools/time_tool.py

from langchain.tools import tool
from datetime import datetime
import pytz

@tool
def get_time(city: str) -> str:
    """Returns the current time in a given city."""
    try:
        city_timezones = {
            "new york": "America/New_York",
            "london": "Europe/London",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney"
        }
        city_key = city.lower()
        if city_key not in city_timezones:
            return f"Sorry, I don't know the timezone for {city}."

        timezone = pytz.timezone(city_timezones[city_key])
        current_time = datetime.now(timezone).strftime("%I:%M %p")
        return f"The current time in {city.title()} is {current_time}."
    except Exception as e:
        return f"Error: {e}"
