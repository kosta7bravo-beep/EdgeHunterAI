import requests
from config import ODDS_API_KEY


BASE_URL = "https://api.odds-api.io/v3/events"


def get_matches():

    if not ODDS_API_KEY:
        raise Exception("ODDS_API_KEY не указан в переменных окружения")

    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "football",
        "status": "pending",
        "limit": 20
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"ODDS API STATUS {response.status_code}: {response.text}"
        )

    data = response.json()

    if isinstance(data, dict) and data.get("error"):
        raise Exception(f"ODDS API ERROR: {data['error']}")

    if not isinstance(data, list):
        raise Exception(f"Неожиданный ответ Odds API: {data}")

    matches = []

    for item in data:

        matches.append({
            "event_id": item.get("id"),
            "league": item.get("league", {}).get("name", ""),
            "home": item.get("home", ""),
            "away": item.get("away", ""),
            "date": item.get("date", ""),
            "status": item.get("status", "")
        })

    return matches
        
