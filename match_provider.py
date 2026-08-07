import requests
from config import FOOTBALL_API_KEY

BASE_URL = "https://v3.football.api-sports.io/fixtures"


def get_matches():
    

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    params = {
        "next": 20
    }

    try:
        print("=== START API REQUEST ===")
        print("KEY LENGTH:", len(FOOTBALL_API_KEY))

        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=5
        )

        print("STATUS:", response.status_code)
        print("URL:", response.url)

        data = response.json()

        print("RESULTS:", len(data.get("response", [])))
        print("ERROR:", data.get("errors"))
        print("MESSAGE:", data.get("message"))

        matches = []

        for item in data.get("response", []):
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

    except Exception as e:
        print("EXCEPTION:", e)
        return []
