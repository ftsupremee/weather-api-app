"""GUI-free client for the OpenWeather "current weather" API.

Every failure is raised as WeatherError with a message that is safe to show to
the user (in particular, it never contains the request URL, which includes the API key).
"""

import os
from dataclasses import dataclass

import requests

API_URL = "https://api.openweathermap.org/data/2.5/weather"
TIMEOUT_SECONDS = 10

HTTP_ERROR_MESSAGES = {
    400: "Bad request. Please check your input.",
    401: "Invalid API key. Check OPENWEATHER_API_KEY in your .env file.",
    403: "Access denied.",
    404: "City not found.",
    429: "Too many requests. Please wait a moment and try again.",
    500: "The weather service had an internal error. Please try again later.",
    502: "Bad gateway: the weather service returned an invalid response.",
    503: "The weather service is unavailable. Please try again later.",
    504: "Gateway timeout: the weather service did not respond.",
}


class WeatherError(Exception):
    """A failure with a user-presentable message."""


@dataclass(frozen=True)
class Weather:
    city: str
    country: str
    temperature_c: float
    description: str
    humidity: int
    wind_speed_ms: float


def get_api_key() -> str:
    """Read the key from the environment (OPENWEATHER_API_KEY, or legacy `api_key`)."""
    key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("api_key")
    if not key:
        raise WeatherError("No API key found. Set OPENWEATHER_API_KEY in a .env file.")
    return key


def fetch_weather(city: str, api_key: str, session=None) -> Weather:
    """Fetch current weather for `city`. Raises WeatherError on any failure."""
    city = city.strip()
    if not city:
        raise WeatherError("Please enter a city name.")

    http = session or requests
    try:
        # `params` URL-encodes the city (the old f-string URL broke on e.g. "São Paulo").
        # `units=metric` returns Celsius directly instead of converting from Kelvin.
        response = http.get(
            API_URL,
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError:
        status = response.status_code
        raise WeatherError(HTTP_ERROR_MESSAGES.get(status, f"HTTP error {status}.")) from None
    except requests.exceptions.Timeout:  # before ConnectionError: ConnectTimeout is both
        raise WeatherError("The request timed out. Please try again.") from None
    except requests.exceptions.ConnectionError:
        raise WeatherError("Connection error. Check your internet connection.") from None
    except requests.exceptions.TooManyRedirects:
        raise WeatherError("Too many redirects from the weather service.") from None
    except ValueError:  # non-JSON body (must precede RequestException: requests' JSONDecodeError is both)
        raise WeatherError("The weather service sent an unreadable response.") from None
    except requests.exceptions.RequestException:
        raise WeatherError("The request failed. Please try again.") from None

    return _parse(data)


def _parse(data: dict) -> Weather:
    try:
        return Weather(
            city=data["name"],
            country=data["sys"]["country"],
            temperature_c=float(data["main"]["temp"]),
            description=data["weather"][0]["description"].capitalize(),
            humidity=int(data["main"]["humidity"]),
            wind_speed_ms=float(data["wind"]["speed"]),
        )
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        raise WeatherError("The weather service sent an unexpected response.") from None
