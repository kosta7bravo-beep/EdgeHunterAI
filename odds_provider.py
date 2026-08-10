import os
import requests
from datetime import datetime, timezone


# =================================================
# THE ODDS API
# =================================================

BASE_URL = "https://api.the-odds-api.com/v4"

ODDS_API_KEY = os.environ.get(
    "ODDS_API_KEY",
    ""
).strip()


# =================================================
# НАСТРОЙКИ
# =================================================

REGIONS = "eu"
MARKETS = "h2h,totals"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"


# =================================================
# ДИАГНОСТИКА API KEY
# =================================================

print(
    "ODDS KEY DEBUG:",
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
# ПРОВЕРКА API KEY
# =================================================

def _check_key():

    if not ODDS_API_KEY:

        raise Exception(
            "ODDS_API_KEY не найден в Environment"
        )


# =================================================
# ОБЩИЙ REQUEST
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
            "ODDS API REQUEST ERROR: "
            + repr(e)
        )

    if response.status_code != 200:

        raise Exception(
            f"ODDS API HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

    try:

        return response.json()

    except Exception as e:

        raise Exception(
            "ODDS API JSON ERROR: "
            + repr(e)
        )


# =================================================
# ПРОВЕРКА ДОСТУПА К API
# =================================================

def test_odds_api():

    data = _request(
        "/sports"
    )

    if not isinstance(
        data,
        list
    ):

        raise Exception(
            "ODDS API: /sports "
            "вернул неожиданный формат"
        )

    print(
        "ODDS API TEST: OK"
    )

    print(
        "ODDS API SPORTS COUNT:",
        len(data)
    )

    return data


# =================================================
# СПИСОК SPORTS
# =================================================

def get_sports():

    return test_odds_api()


# =================================================
# ПОИСК ФУТБОЛЬНЫХ SPORT KEYS
# =================================================

def get_football_sport_keys():

    sports = get_sports()

    football = []

    for sport in sports:

        if not isinstance(
            sport,
            dict
        ):
            continue

        key = str(
            sport.get(
                "key",
                ""
            )
        )

        group = str(
            sport.get(
                "group",
                ""
            )
        ).lower()

        title = str(
            sport.get(
                "title",
                ""
            )
        ).lower()

        description = str(
            sport.get(
                "description",
                ""
            )
        ).lower()

        text = (
            group
            + " "
            + title
            + " "
            + description
        )

        if (
            "soccer" in text
            or "football" in text
        ):

            if key:

                football.append(
                    {
                        "key": key,
                        "title": sport.get(
                            "title",
                            key
                        ),
                        "group": sport.get(
                            "group",
                            ""
                        )
                    }
                )

    print(
        "ODDS FOOTBALL SPORTS:",
        football
    )

    return football


# =================================================
# ПОЛУЧЕНИЕ КОЭФФИЦИЕНТОВ
# =================================================

def get_odds_for_sport(
    sport_key
):

    if not sport_key:

        raise Exception(
            "ODDS API: пустой sport_key"
        )

    data = _request(
        f"/sports/{sport_key}/odds",
        {
            "regions": REGIONS,
            "markets": MARKETS,
            "oddsFormat": ODDS_FORMAT,
            "dateFormat": DATE_FORMAT
        }
    )

    if not isinstance(
        data,
        list
    ):

        raise Exception(
            f"ODDS API: /sports/"
            f"{sport_key}/odds "
            "вернул неожиданный формат"
        )

    print(
        "ODDS SPORT:",
        sport_key,
        "MATCHES:",
        len(data)
    )

    return data


# =================================================
# ПОЛУЧЕНИЕ ФУТБОЛЬНЫХ МАТЧЕЙ
# =================================================

def get_odds_matches():

    football_sports = (
        get_football_sport_keys()
    )

    if not football_sports:

        raise Exception(
            "ODDS API: "
            "футбольные sport_key "
            "не найдены"
        )

    all_matches = []

    for sport in football_sports:

        sport_key = sport["key"]

        try:

            matches = get_odds_for_sport(
                sport_key
            )

            for match in matches:

                if not isinstance(
                    match,
                    dict
                ):
                    continue

                match["_sport_key"] = (
                    sport_key
                )

                match["_sport_title"] = (
                    sport.get(
                        "title",
                        sport_key
                    )
                )

                all_matches.append(
                    match
                )

        except Exception as e:

            print(
                "ODDS SPORT ERROR:",
                sport_key,
                repr(e)
            )

    # Убираем дубликаты

    unique = {}

    for match in all_matches:

        match_id = match.get(
            "id"
        )

        if match_id:

            unique[
                match_id
            ] = match

    matches = list(
        unique.values()
    )

    # Ближайшие матчи сначала

    matches.sort(
        key=lambda item:
            item.get(
                "commence_time",
                ""
            )
    )

    print(
        "ODDS TOTAL UNIQUE MATCHES:",
        len(matches)
    )

    return matches


# =================================================
# ДАТА МАТЧА
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
# H2H / 1X2
# =================================================

def extract_h2h(
    bookmakers
):

    results = []

    for bookmaker in (
        bookmakers or []
    ):

        if not isinstance(
            bookmaker,
            dict
        ):
            continue

        bookmaker_name = (
            bookmaker.get(
                "title",
                "—"
            )
        )

        for market in (
            bookmaker.get(
                "markets",
                []
            )
        ):

            if not isinstance(
                market,
                dict
            ):
                continue

            if market.get(
                "key"
            ) != "h2h":

                continue

            for outcome in (
                market.get(
                    "outcomes",
                    []
                )
            ):

                if not isinstance(
                    outcome,
                    dict
                ):
                    continue

                name = outcome.get(
                    "name"
                )

                price = outcome.get(
                    "price"
                )

                if (
                    name
                    and price is not None
                ):

                    try:

                        price = float(
                            price
                        )

                    except Exception:

                        continue

                    results.append(
                        {
                            "name": name,
                            "odds": price,
                            "bookmaker":
                                bookmaker_name
                        }
                    )

    return results


# =================================================
# TOTALS
# =================================================

def extract_totals(
    bookmakers
):

    results = []

    for bookmaker in (
        bookmakers or []
    ):

        if not isinstance(
            bookmaker,
            dict
        ):
            continue

        bookmaker_name = (
            bookmaker.get(
                "title",
                "—"
            )
        )

        for market in (
            bookmaker.get(
                "markets",
                []
            )
        ):

            if not isinstance(
                market,
                dict
            ):
                continue

            if market.get(
                "key"
            ) != "totals":

                continue

            for outcome in (
                market.get(
                    "outcomes",
                    []
                )
            ):

                if not isinstance(
                    outcome,
                    dict
                ):
                    continue

                name = outcome.get(
                    "name"
                )

                point = outcome.get(
                    "point"
                )

                price = outcome.get(
                    "price"
                )

                if (
                    name
                    and point is not None
                    and price is not None
                ):

                    try:

                        point = float(
                            point
                        )

                        price = float(
                            price
                        )

                    except Exception:

                        continue

                    results.append(
                        {
                            "name": name,
                            "point": point,
                            "odds": price,
                            "bookmaker":
                                bookmaker_name
                        }
                    )

    return results
