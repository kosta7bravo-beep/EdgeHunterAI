import os
import requests
from datetime import datetime, timezone


BASE_URL = "https://api.the-odds-api.com/v4"

ODDS_API_KEY = os.environ.get(
    "ODDS_API_KEY",
    ""
).strip()


def get_odds_matches():

    if not ODDS_API_KEY:
        raise Exception(
            "ODDS_API_KEY не найден в Environment"
        )

    response = requests.get(
        f"{BASE_URL}/sports/soccer/odds",
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h,totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        },
        timeout=30,
    )

    if response.status_code != 200:

        raise Exception(
            f"ODDS API HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    data = response.json()

    if not isinstance(data, list):
        raise Exception(
            "ODDS API: неожиданный формат ответа"
        )

    return data
