import requests
from config import ODDS_API_KEY

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


def get_odds():

    response = requests.get(
        BASE_URL,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h"
        },
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(f"ODDS API ERROR {response.status_code}")

    return response.json()
