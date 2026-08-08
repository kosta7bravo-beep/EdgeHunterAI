import time
import requests
from config import ODDS_API_KEY


EVENTS_URL = "https://api.odds-api.io/v3/events"
ODDS_URL = "https://api.odds-api.io/v3/odds/multi"

BOOKMAKERS = "Bet365,Betway"

EVENTS_CACHE_TIME = 1800

_cached_events = []
_last_events_update = 0


def get_events():
    global _cached_events
    global _last_events_update

    now = time.time()

    if (
        _cached_events
        and now - _last_events_update < EVENTS_CACHE_TIME
    ):
        return _cached_events

    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "football",
        "status": "pending"
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

    data = response.json()

    if isinstance(data, dict) and data.get("error"):
        raise Exception(
            f"EVENTS API ERROR: {data['error']}"
        )

    if not isinstance(data, list):
        raise Exception(
            f"Неожиданный ответ events: {data}"
        )

    _cached_events = data[:10]
    _last_events_update = now

    return _cached_events


def get_odds(event_ids):
    if not event_ids:
        return {}

    params = {
        "apiKey": ODDS_API_KEY,
        "eventIds": ",".join(
            str(event_id)
            for event_id in event_ids[:10]
        ),
        "bookmakers": BOOKMAKERS
    }

    response = requests.get(
        ODDS_URL,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"ODDS API STATUS {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if isinstance(data, dict) and data.get("error"):
        raise Exception(
            f"ODDS API ERROR: {data['error']}"
        )

    if not isinstance(data, list):
        raise Exception(
            f"Неожиданный ответ odds/multi: {data}"
        )

    result = {}

    for event in data:
        event_id = event.get("id")

        if event_id:
            result[event_id] = event

    return result


def get_matches():

    if not ODDS_API_KEY:
        raise Exception(
            "ODDS_API_KEY не указан в переменных окружения"
        )

    events = get_events()

    if not events:
        return []

    event_ids = [
        event.get("id")
        for event in events
        if event.get("id")
    ]

    odds_data = get_odds(event_ids)

    matches = []

    for event in events:

        event_id = event.get("id")
        odds_event = odds_data.get(event_id, {})

        matches.append({
            "event_id": event_id,

            "league": event.get(
                "league", {}
            ).get("name", ""),

            "home": event.get("home", ""),

            "away": event.get("away", ""),

            "date": event.get("date", ""),

            "status": event.get("status", ""),

            "odds_data": odds_event.get(
                "bookmakers", {}
            )
        })

    return matches
