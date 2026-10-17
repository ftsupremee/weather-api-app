# Weather App

A small PyQt5 desktop app that shows the current weather for any city, using the
[OpenWeather](https://openweathermap.org/current) API.

- Press **Enter** or click **Get weather**; shows temperature (°C), conditions, humidity and wind
- The request runs in a background thread, so the window never freezes
- 10-second timeout and friendly messages for bad keys, unknown cities, rate limits and network problems
- API key is read from `.env` and never shown in error messages

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then paste your OpenWeather API key into .env
python main.py
```

Get a free key at https://home.openweathermap.org/api_keys (new keys can take a little while to activate).

## Layout

```
main.py                     PyQt5 window + background thread
weather_client.py           API call, parsing and error handling (no Qt, fully testable)
tests/test_weather_client.py
```

## Tests

```bash
python -m unittest discover -s tests
```

The tests mock the network, so they need no API key and no Qt.
