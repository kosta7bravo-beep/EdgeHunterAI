import requests
from config import FOOTBALL_API_KEY

BASE_URL = "https://v3.football.api-sports.io/fixtures"


def get_matches():

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    params = {
        "date": "2026-08-07"
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"API STATUS {response.status_code}")

    data = response.json()

    if data.get("errors"):
        raise Exception(f"API ERRORS: {data['errors']}")

    if "response" not in data:
        raise Exception("В ответе нет response")

    matches = []

    for item in data["response"]:

        matches.append({
            "league": item["league"]["name"],
            "home": item["teams"]["home"]["name"],
            "away": item["teams"]["away"]["name"],
            "date": item["fixture"]["date"],
            "odd": 2.0,
            "home_form": 3,
            "away_form": 3,
            "goals_avg": 2.5
        })

    return matches
        
