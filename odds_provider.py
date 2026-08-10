import os
import requests
from datetime import datetime, timezone


# =================================================
# ODDS-API.IO
# =================================================

BASE_URL = "https://api.odds-api.io/v3"

ODDS_API_KEY = os.environ.get(
    "ODDS_API_KEY",
    ""
).strip()


# =================================================
# НАСТРОЙКИ
# =================================================

SPORT = "football"

BOOKMAKERS = "Bet365,Betway"

EVENT_LIMIT = 20


# =================================================
# ДИАГНОСТИКА
# =================================================

print(
    "ODDS-API.IO KEY DEBUG:",
    {
        "exists": bool(ODDS_API_KEY),
        "length": len(ODDS_API_KEY),
        "prefix": ODDS_API_KEY[:8],
        "suffix": (
            ODDS_API_KEY[-4:]
            if ODDS_API_KEY
            else ""
        )
    }
)


# =================================================
# ПРОВЕРКА КЛЮЧА
# =================================================

def _check_key():

    if not ODDS_API_KEY:

        raise Exception(
            "ODDS_API_KEY не найден в Environment"
        )


# =================================================
# REQUEST
# =================================================

def _request(
    endpoint,
    params=None
):

    _check_key()

    request_params = dict(
        params or {}
    )

    request_params["apiKey"] = (
        ODDS_API_KEY
    )

    try:

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            params=request_params,
            timeout=30
        )

    except Exception as e:

        raise Exception(
            "ODDS-API.IO REQUEST ERROR: "
            + repr(e)
        )

    if response.status_code != 200:

        raise Exception(
            f"ODDS-API.IO HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

    try:

        return response.json()

    except Exception as e:

        raise Exception(
            "ODDS-API.IO JSON ERROR: "
            + repr(e)
        )


# =================================================
# SPORTS
# =================================================

def get_sports():

    data = requests.get(
        f"{BASE_URL}/sports",
        timeout=30
    )

    if data.status_code != 200:

        raise Exception(
            f"ODDS-API.IO SPORTS HTTP "
            f"{data.status_code}: "
            f"{data.text[:500]}"
        )

    result = data.json()

    if not isinstance(
        result,
        list
    ):

        raise Exception(
            "ODDS-API.IO: "
            "/sports вернул "
            "неожиданный формат"
        )

    return result


# =================================================
# EVENTS
# =================================================

def get_events(
    limit=EVENT_LIMIT
):

    data = _request(
        "/events",
        {
            "sport": SPORT,
            "status": "pending",
            "limit": limit
        }
    )

    if not isinstance(
        data,
        list
    ):

        raise Exception(
            "ODDS-API.IO: "
            "/events вернул "
            "неожиданный формат"
        )

    print(
        "ODDS-API.IO EVENTS:",
        len(data)
    )

    return data


# =================================================
# ODDS ДЛЯ ОДНОГО МАТЧА
# =================================================

def get_event_odds(
    event_id
):

    if not event_id:

        raise Exception(
            "ODDS-API.IO: "
            "отсутствует eventId"
        )

    data = _request(
        "/odds",
        {
            "eventId": event_id,
            "bookmakers": BOOKMAKERS
        }
    )

    if not isinstance(
        data,
        dict
    ):

        raise Exception(
            "ODDS-API.IO: "
            "/odds вернул "
            "неожиданный формат"
        )

    return data


# =================================================
# ВСЕ БЛИЖАЙШИЕ МАТЧИ + ODDS
# =================================================

def get_odds_matches(
    limit=EVENT_LIMIT
):

    events = get_events(
        limit=limit
    )

    result = []

    for event in events:

        if not isinstance(
            event,
            dict
        ):
            continue

        event_id = event.get(
            "id"
        )

        if not event_id:
            continue

        try:

            odds = get_event_odds(
                event_id
            )

            item = dict(event)

            item["odds"] = odds

            result.append(
                item
            )

        except Exception as e:

            print(
                "ODDS-API.IO ODDS ERROR:",
                event_id,
                repr(e)
            )

    print(
        "ODDS-API.IO MATCHES WITH ODDS:",
        len(result)
    )

    return result


# =================================================
# ФОРМАТ ДАТЫ
# =================================================

def format_match_date(
    value
):

    if not value:

        return "—"

    try:

        dt = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00"
            )
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        ).strftime(
            "%d.%m.%Y %H:%M UTC"
        )

    except Exception:

        return str(value)


# =================================================
# ИЗВЛЕЧЕНИЕ КОЭФФИЦИЕНТОВ
# =================================================

def extract_odds(
    event
):

    odds_data = (
        event.get("odds")
        or {}
    )

    bookmakers = (
        odds_data.get(
            "bookmakers",
            {}
        )
    )

    result = []

    if not isinstance(
        bookmakers,
        dict
    ):

        return result

    for bookmaker_name, markets in (
        bookmakers.items()
    ):

        if not isinstance(
            markets,
            list
        ):
            continue

        for market in markets:

            if not isinstance(
                market,
                dict
            ):
                continue

            market_name = market.get(
                "name"
            )

            market_odds = market.get(
                "odds"
            )

            if not isinstance(
                market_odds,
                list
            ):
                continue

            for odd in market_odds:

                if not isinstance(
                    odd,
                    dict
                ):
                    continue

                result.append(
                    {
                        "bookmaker":
                            bookmaker_name,

                        "market":
                            market_name,

                        "odds":
                            odd
                    }
                )

    return result


# =================================================
# КРАТКАЯ ИНФОРМАЦИЯ О МАТЧЕ
# =================================================

def match_summary(
    event
):

    home = event.get(
        "home",
        "—"
    )

    away = event.get(
        "away",
        "—"
    )

    date = format_match_date(
        event.get(
            "date"
        )
    )

    league = event.get(
        "league"
    )

    if isinstance(
        league,
        dict
    ):

        league_name = (
            league.get(
                "name"
            )
            or league.get(
                "slug"
            )
            or "—"
        )

    else:

        league_name = str(
            league or "—"
        )

    return (
        f"⚽ {home} — {away}\n"
        f"🏆 {league_name}\n"
        f"📅 {date}"
)
