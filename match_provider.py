import requests
from config import API_KEY

BASE_URL = "https://v3.football.api-sports.io/fixtures"

def get_matches():
    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "next": 20
    }

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=20)

        if response.status_code != 200:
            print("Ошибка API:", response.status_code)
            return []

        data = response.json()

        matches = []

        for item in data.get("response", []):
            matches.append({
                "league": item["league"]["name"],
                "home": item["teams"]["home"]["name"],
                "away": item["teams"]["away"]["name"],
                "odd": 2.0,
                "home_form": 3,
                "away_form": 3,
                "goals_avg": 2.5
            })

        return matches

    except Exception as e:
        print("Ошибка получения матчей:", e)
        return []
