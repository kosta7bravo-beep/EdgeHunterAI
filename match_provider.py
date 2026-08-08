import requests
from config import ODDS_API_KEY


EVENTS_URL = "https://api.odds-api.io/v3/events"
ODDS_URL = "https://api.odds-api.io/v3/odds/multi"


def get_odds(event_ids):

    if not event_ids:
        return {}

    params = {
        "apiKey": ODDS_API_KEY,
        "eventIds": ",".join(str(x) for x in event_ids[:10])
    }

    response = requests.get(
        ODDS_URL,
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
        raise Exception(f"Неожиданный ответ odds/multi: {data}")

    result = {}

    for event in data:

        event_id = event.get("id")

        if not event_id:
            continue

        event_odds = {
            "home": None,
            "draw": None,
            "away": None,
            "over_2_5": None,
            "under_2_5": None
        }

        bookmakers = event.get("bookmakers", {})

        for bookmaker_markets in bookmakers.values():

            for market in bookmaker_markets:

                market_name = market.get("name")
                odds_list = market.get("odds", [])

                if not odds_list:
                    continue

                odds = odds_list[0]

                # Победа / ничья / победа гостей
                if market_name == "ML":

                    if odds.get("home"):
                        event_odds["home"] = float(odds["home"])

                    if odds.get("draw"):
                        event_odds["draw"] = float(odds["draw"])

                    if odds.get("away"):
                        event_odds["away"] = float(odds["away"])

                # Тотал
                elif market_name == "Totals":

                    hdp = odds.get("hdp")

                    if hdp == 2.5:

                        if odds.get("over"):
                            event_odds["over_2_5"] = float(
                                odds["over"]
                            )

                        if odds.get("under"):
                            event_odds["under_2_5"] = float(
                                odds["under"]
                            )

        result[event_id] = event_odds

    return result


def get_matches():

    if not ODDS_API_KEY:
        raise Exception(
            "ODDS_API_KEY не указан в переменных окружения"
        )

    # Получаем ближайшие футбольные матчи
    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "football",
        "status": "pending",
        "limit": 10
    }

    response = requests.get(
        EVENTS_URL,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"EVENTS API STATUS {response.status_code}: "
            f"{response.text}"
        )

    events = response.json()

    if isinstance(events, dict) and events.get("error"):
        raise Exception(
            f"EVENTS API ERROR: {events['error']}"
        )

    if not isinstance(events, list):
        raise Exception(
            f"Неожиданный ответ events: {events}"
        )

    if not events:
        return []

    # ID матчей
    event_ids = [
        event.get("id")
        for event in events
        if event.get("id")
    ]

    # Один batch-запрос коэффициентов
    odds_data = get_odds(event_ids)

    matches = []

    for event in events:

        event_id = event.get("id")

        odds = odds_data.get(
            event_id,
            {}
        )

        matches.append({
            "event_id": event_id,

            "league": event.get(
                "league", {}
            ).get("name", ""),

            "home": event.get("home", ""),

            "away": event.get("away", ""),

            "date": event.get("date", ""),

            "status": event.get("status", ""),

            "home_odds": odds.get("home"),

            "draw_odds": odds.get("draw"),

            "away_odds": odds.get("away"),

            "over_2_5": odds.get("over_2_5"),

            "under_2_5": odds.get("under_2_5")
        })

    return matches
        
