import time
import requests
from config import ODDS_API_KEY


EVENTS_URL = "https://api.odds-api.io/v3/events"
ODDS_URL = "https://api.odds-api.io/v3/odds/multi"

# Обновляем список матчей раз в 30 минут
EVENTS_CACHE_TIME = 1800

_cached_events = []
_last_events_update = 0


def get_events():

    global _cached_events
    global _last_events_update

    now = time.time()

    # Используем сохранённые события
    if _cached_events and now - _last_events_update < EVENTS_CACHE_TIME:
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

    # Берём максимум 10 событий
    _cached_events = data[:10]
    _last_events_update = now

    return _cached_events


def get_odds(event_ids):

    if not event_ids:
        return {}

    params = {
        "apiKey": ODDS_API_KEY,
        "eventIds": ",".join(
            str(x) for x in event_ids[:10]
        )
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

        if not event_id:
            continue

        result[event_id] = event

    return result


def get_matches():

    if not ODDS_API_KEY:
        raise Exception(
            "ODDS_API_KEY не указан"
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

        odds_event = odds_data.get(
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

            "odds_data": odds_event.get(
                "bookmakers", {}
            )
        })

    return matches
