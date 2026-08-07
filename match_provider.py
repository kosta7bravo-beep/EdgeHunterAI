import requests
from datetime import datetime
from config import FOOTBALL_API_KEY

BASE_URL = "https://v3.football.api-sports.io/fixtures"


def get_matches():
    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    params = {
    "live": "all"
    }
    }

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            print("Ошибка API:", response.status_code)
            return []

        data = response.json()

        matches = []

        for item in data.get("response", []):

            fixture_date = item["fixture"]["date"]

            dt = datetime.fromisoformat(
                fixture_date.replace("Z", "+00:00")
            )

            matches.append({
                "league": item["league"]["name"],
                "home": item["teams"]["home"]["name"],
                "away": item["teams"]["away"]["name"],

                "date": dt.strftime("%d.%m.%Y"),
                "time": dt.strftime("%H:%M"),

                # Пока оставляем тестовые значения.
                # Позже заменим их реальными.
                "odd": 2.00,
                "home_form": 3,
                "away_form": 3,
                "goals_avg": 2.5
            })

        return matches

    except Exception as e:
        print("Ошибка получения матчей:", e)
        return []
