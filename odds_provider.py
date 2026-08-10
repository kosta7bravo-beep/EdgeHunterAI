import os
import requests
from datetime import datetime, timezone


# =========================================================
# THE ODDS API
# =========================================================

BASE_URL = "https://api.the-odds-api.com/v4"

ODDS_API_KEY = os.getenv(
    "ODDS_API_KEY",
    ""
).strip().strip('"').strip("'")


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOOKMAKERS = "bet365,betway"

REGIONS = "eu"

MARKETS = "h2h,totals"

ODDS_FORMAT = "decimal"

DATE_FORMAT = "iso"

REQUEST_TIMEOUT = 30


# =========================================================
# API KEY
# =========================================================

def _get_api_key():

    key = (
        os.getenv(
            "ODDS_API_KEY",
            ""
        )
        .strip()
        .strip('"')
        .strip("'")
    )

    if not key:
        raise Exception(
            "ODDS_API_KEY не найден в Environment"
        )

    return key


# =========================================================
# GET REQUEST
# =========================================================

def _request(
    endpoint,
    params=None
):

    key = _get_api_key()

    request_params = dict(
        params or {}
    )

    request_params["apiKey"] = key

    try:

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            params=request_params,
            timeout=REQUEST_TIMEOUT
        )

    except requests.RequestException as e:

        raise Exception(
            "ODDS API REQUEST ERROR: "
            + str(e)
        )

    if response.status_code != 200:

        # Не показываем API key в ошибке
        text = response.text[:1000]

        raise Exception(
            f"ODDS API HTTP "
            f"{response.status_code}: "
            f"{text}"
        )

    try:

        return response.json()

    except ValueError:

        raise Exception(
            "ODDS API JSON ERROR: "
            "сервер вернул не JSON"
        )


# =========================================================
# ДОСТУПНЫЕ SPORTS
# =========================================================

def get_sports():

    data = _request(
        "/sports"
    )

    if not isinstance(
        data,
        list
    ):

        raise Exception(
            "ODDS API SPORTS: "
            "неожиданный формат"
        )

    return data


# =========================================================
# ФУТБОЛЬНЫЕ SPORTS
# =========================================================

def get_football_sports():

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

        if (
            key.startswith(
                "soccer_"
            )
            or group == "soccer"
            or "soccer" in title
            or "football" in title
        ):

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
                    ),
                    "active": sport.get(
                        "active",
                        False
                    )
                }
            )

    return football


# =========================================================
# ПРИОРИТЕТНЫЕ ФУТБОЛЬНЫЕ ЛИГИ
# =========================================================

PRIORITY_KEYS = [

    "soccer_epl",

    "soccer_germany_bundesliga",

    "soccer_italy_serie_a",

    "soccer_spain_la_liga",

    "soccer_france_ligue_one",

    "soccer_uefa_champs_league",

    "soccer_uefa_europa_league",

    "soccer_uefa_europa_conference_league",

    "soccer_netherlands_eredivisie",

    "soccer_portugal_primeira_liga",

    "soccer_belgium_first_div",

    "soccer_turkey_super_league",

    "soccer_greece_super_league",

    "soccer_scotland_premiership",

]


# =========================================================
# ВЫБОР SPORT KEYS
# =========================================================

def get_priority_football_keys():

    available = (
        get_football_sports()
    )

    available_keys = {
        item["key"]
        for item in available
    }

    result = []

    for key in PRIORITY_KEYS:

        if key in available_keys:

            result.append(key)

    return result


# =========================================================
# КОЭФФИЦИЕНТЫ ОДНОЙ ЛИГИ
# =========================================================

def get_odds_for_sport(
    sport_key
):

    if not sport_key:

        raise Exception(
            "ODDS API: "
            "sport_key пустой"
        )

    data = _request(
        f"/sports/{sport_key}/odds",
        {
            "regions": REGIONS,
            "markets": MARKETS,
            "oddsFormat": ODDS_FORMAT,
            "dateFormat": DATE_FORMAT,
            "bookmakers": BOOKMAKERS
        }
    )

    if not isinstance(
        data,
        list
    ):

        raise Exception(
            "ODDS API ODDS: "
            "неожиданный формат"
        )

    return data


# =========================================================
# ДАТА
# =========================================================

def _parse_datetime(
    value
):

    if not value:

        return None

    try:

        text = str(
            value
        ).strip()

        text = text.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            text
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:

        return None


# =========================================================
# НАЗВАНИЕ КОМАНДЫ
# =========================================================

def _team_name(
    value
):

    if isinstance(
        value,
        str
    ):

        return value

    if isinstance(
        value,
        dict
    ):

        return (
            value.get("name")
            or value.get("title")
            or value.get("short_name")
            or ""
        )

    return str(
        value or ""
    )


# =========================================================
# НОРМАЛИЗАЦИЯ МАТЧА
# =========================================================

def normalize_match(
    match
):

    if not isinstance(
        match,
        dict
    ):

        return None

    home = _team_name(
        match.get(
            "home_team"
        )
    )

    away = _team_name(
        match.get(
            "away_team"
        )
    )

    if not home or not away:

        return None

    kickoff = _parse_datetime(
        match.get(
            "commence_time"
        )
    )

    return {

        "id": match.get(
            "id"
        ),

        "sport_key": match.get(
            "sport_key"
        ),

        "sport_title": match.get(
            "sport_title"
        ),

        "home": home,

        "away": away,

        "kickoff_utc": (
            kickoff.isoformat()
            if kickoff
            else ""
        ),

        "bookmakers":
            match.get(
                "bookmakers",
                []
            )
    }


# =========================================================
# ВСЕ МАТЧИ С КОЭФФИЦИЕНТАМИ
# =========================================================

def get_odds_matches(
    sport_keys=None
):

    if sport_keys is None:

        sport_keys = (
            get_priority_football_keys()
        )

    if not sport_keys:

        raise Exception(
            "ODDS API: "
            "не найдено доступных "
            "футбольных sport_key"
        )

    all_matches = []

    errors = []

    for sport_key in sport_keys:

        try:

            matches = (
                get_odds_for_sport(
                    sport_key
                )
            )

            for match in matches:

                normalized = (
                    normalize_match(
                        match
                    )
                )

                if normalized:

                    all_matches.append(
                        normalized
                    )

        except Exception as e:

            errors.append(
                f"{sport_key}: {e}"
            )

    # Если API не дал ни одного матча
    if not all_matches:

        message = (
            "ODDS API: "
            "не получено ни одного матча."
        )

        if errors:

            message += (
                "\n\n"
                + "\n".join(
                    errors[:10]
                )
            )

        raise Exception(
            message
        )

    # Убираем дубликаты
    unique = {}

    for match in all_matches:

        match_id = (
            match.get(
                "id"
            )
            or (
                match.get(
                    "home",
                    ""
                )
                + "_"
                + match.get(
                    "away",
                    ""
                )
                + "_"
                + match.get(
                    "kickoff_utc",
                    ""
                )
            )
        )

        unique[
            match_id
        ] = match

    result = list(
        unique.values()
    )

    # Сначала ближайшие матчи
    result.sort(
        key=lambda item:
        item.get(
            "kickoff_utc",
            "9999"
        )
    )

    return result


# =========================================================
# ИЗВЛЕЧЕНИЕ КОЭФФИЦИЕНТОВ
# =========================================================

def extract_odds(
    match
):

    result = {

        "h2h": {},

        "totals": {}
    }

    bookmakers = (
        match.get(
            "bookmakers"
        )
        or []
    )

    for bookmaker in bookmakers:

        bookmaker_name = (
            bookmaker.get(
                "title"
            )
            or bookmaker.get(
                "key"
            )
            or ""
        )

        markets = (
            bookmaker.get(
                "markets"
            )
            or []
        )

        for market in markets:

            market_key = market.get(
                "key"
            )

            outcomes = (
                market.get(
                    "outcomes"
                )
                or []
            )

            # -------------------------
            # 1X2
            # -------------------------

            if market_key == "h2h":

                for outcome in outcomes:

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

                        result[
                            "h2h"
                        ].setdefault(
                            name,
                            []
                        ).append(
                            {
                                "bookmaker":
                                    bookmaker_name,
                                "odds":
                                    price
                            }
                        )

            # -------------------------
            # TOTALS
            # -------------------------

            elif market_key == "totals":

                for outcome in outcomes:

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
                        and price is not None
                    ):

                        result[
                            "totals"
                        ].setdefault(
                            name,
                            []
                        ).append(
                            {
                                "bookmaker":
                                    bookmaker_name,

                                "point":
                                    point,

                                "odds":
                                    price
                            }
                        )

    return result


# =========================================================
# УДОБНЫЙ ФОРМАТ ДЛЯ БОТА
# =========================================================

def format_match(
    match
):

    odds = extract_odds(
        match
    )

    return {

        "id":
            match.get(
                "id"
            ),

        "league":
            match.get(
                "sport_title"
            ),

        "sport_key":
            match.get(
                "sport_key"
            ),

        "home":
            match.get(
                "home"
            ),

        "away":
            match.get(
                "away"
            ),

        "kickoff_utc":
            match.get(
                "kickoff_utc"
            ),

        "odds":
            odds
    }


# =========================================================
# ПРОВЕРКА ODDS API
# =========================================================

def check_odds_api():

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

        if key.startswith(
            "soccer_"
        ):

            football.append(
                key
            )

    return {

        "status": "OK",

        "sports_total":
            len(sports),

        "football_sports":
            football
}
