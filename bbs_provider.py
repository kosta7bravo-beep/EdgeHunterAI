import os
import time
import requests
from datetime import datetime, timezone, timedelta


BASE_URL = "https://api.bigballsdata.com/v1"

BBS_API_KEY = os.environ.get("BBS_API_KEY", "").strip()

# Матчи обновляем каждые 30 минут
MATCHES_CACHE_TIME = 1800

# Статистика команд живет 6 часов
TEAM_CACHE_TIME = 21600

# Берем только ближайшие 14 дней
MATCHES_DAYS_AHEAD = 14

_cached_matches = None
_cached_matches_time = 0

_team_cache = {}


def _headers():
    if not BBS_API_KEY:
        raise Exception(
            "BBS_API_KEY не найден в Environment"
        )

    return {
        "Authorization": "Bearer " + BBS_API_KEY,
        "Accept": "application/json",
    }


def _request(url, params=None):

    try:
        response = requests.get(
            url,
            headers=_headers(),
            params=params or {},
            timeout=20
        )

    except Exception as e:
        raise Exception(
            "BBS REQUEST ERROR: "
            + repr(e)
        )

    if response.status_code != 200:

        try:
            body = response.text[:500]
        except Exception:
            body = "<response decode error>"

        raise Exception(
            f"BBS HTTP {response.status_code}: {body}"
        )

    try:
        data = response.json()

    except Exception as e:
        raise Exception(
            "BBS JSON ERROR: "
            + repr(e)
        )

    if not isinstance(data, dict):
        raise Exception(
            "BBS: ответ не является JSON-объектом"
        )

    if data.get("error"):
        raise Exception(
            "BBS API ERROR: "
            + str(data["error"])
        )

    return data


# -------------------------------------------------
# ПОЛУЧЕНИЕ БЛИЖАЙШИХ МАТЧЕЙ
# -------------------------------------------------

def get_matches(limit=50):

    global _cached_matches
    global _cached_matches_time

    now_timestamp = time.time()

    if (
        _cached_matches is not None
        and now_timestamp - _cached_matches_time
        < MATCHES_CACHE_TIME
    ):
        return _cached_matches

    now = datetime.now(timezone.utc)

    max_date = now + timedelta(
        days=MATCHES_DAYS_AHEAD
    )

    data = _request(
        f"{BASE_URL}/matches",
        {
            "sport": "football",
            "limit": 50
        }
    )

    matches = data.get("data", [])

    if not isinstance(matches, list):
        raise Exception(
            "BBS: поле data не является списком"
        )

    filtered_matches = []

    for match in matches:

        date_string = (
            match.get("kickoff_utc")
            or match.get("date")
            or match.get("start_time")
            or match.get("commence_time")
        )

        if not date_string:
            continue

        try:

            match_date = datetime.fromisoformat(
                str(date_string).replace(
                    "Z",
                    "+00:00"
                )
            )

            if match_date.tzinfo is None:
                match_date = match_date.replace(
                    tzinfo=timezone.utc
                )

            match_date = match_date.astimezone(
                timezone.utc
            )

        except Exception:
            continue

        # Матч уже прошел
        if match_date < now:
            continue

        # Матч слишком далеко в будущем
        if match_date > max_date:
            continue

        filtered_matches.append(
            (
                match_date,
                match
            )
        )

    # Сортируем по времени начала
    filtered_matches.sort(
        key=lambda item: item[0]
    )

    # Оставляем только ближайшие
    result = [
        item[1]
        for item in filtered_matches[:limit]
    ]

    _cached_matches = result
    _cached_matches_time = now_timestamp

    return result


# -------------------------------------------------
# ПОИСК КОМАНДЫ
# -------------------------------------------------

def find_team(team_name):

    if not team_name:
        return None

    clean_name = str(
        team_name
    ).strip()

    cache_key = clean_name.lower()

    cached = _team_cache.get(
        f"team:{cache_key}"
    )

    if cached:
        return cached.get("team")

    data = _request(
        f"{BASE_URL}/teams",
        {
            "sport": "football",
            "name": clean_name,
            "limit": 10
        }
    )

    teams = data.get(
        "data",
        []
    )

    if not isinstance(teams, list):
        teams = []

    team = None

    # Сначала ищем точное совпадение
    for item in teams:

        name = str(
            item.get(
                "name",
                ""
            )
        ).strip().lower()

        if name == cache_key:
            team = item
            break

    # Если точного совпадения нет,
    # используем первый результат
    if team is None and teams:
        team = teams[0]

    _team_cache[
        f"team:{cache_key}"
    ] = {
        "time": time.time(),
        "team": team
    }

    return team


# -------------------------------------------------
# ФОРМА КОМАНДЫ
# -------------------------------------------------

def get_team_form(
    team_id,
    limit=10
):

    if not team_id:
        return None

    cache_key = (
        f"form:{team_id}:{limit}"
    )

    cached = _team_cache.get(
        cache_key
    )

    if cached:

        if (
            time.time()
            - cached["time"]
            < TEAM_CACHE_TIME
        ):
            return cached["data"]

    data = _request(
        f"{BASE_URL}/teams/{team_id}/form",
        {
            "limit": limit
        }
    )

    result = data.get(
        "data",
        []
    )

    if not isinstance(
        result,
        list
    ):
        result = []

    _team_cache[
        cache_key
    ] = {
        "time": time.time(),
        "data": result
    }

    return result


# -------------------------------------------------
# СТАТИСТИКА КОМАНДЫ
# -------------------------------------------------

def get_team_stats(team_id):

    if not team_id:
        return None

    cache_key = (
        f"stats:{team_id}"
    )

    cached = _team_cache.get(
        cache_key
    )

    if cached:

        if (
            time.time()
            - cached["time"]
            < TEAM_CACHE_TIME
        ):
            return cached["data"]

    data = _request(
        f"{BASE_URL}/teams/{team_id}/stats"
    )

    result = data.get(
        "data"
    )

    _team_cache[
        cache_key
    ] = {
        "time": time.time(),
        "data": result
    }

    return result


# -------------------------------------------------
# ДАННЫЕ ДВУХ КОМАНД
# -------------------------------------------------

def get_teams_analysis(
    home_name,
    away_name
):

    home_team = find_team(
        home_name
    )

    away_team = find_team(
        away_name
    )

    result = {
        "home": {
            "name": home_name,
            "team": home_team,
            "form": [],
            "stats": None
        },

        "away": {
            "name": away_name,
            "team": away_team,
            "form": [],
            "stats": None
        }
    }

    # Хозяева
    if (
        home_team
        and home_team.get("id")
    ):

        team_id = home_team["id"]

        result["home"]["form"] = (
            get_team_form(
                team_id
            )
        )

        result["home"]["stats"] = (
            get_team_stats(
                team_id
            )
        )

    # Гости
    if (
        away_team
        and away_team.get("id")
    ):

        team_id = away_team["id"]

        result["away"]["form"] = (
            get_team_form(
                team_id
            )
        )

        result["away"]["stats"] = (
            get_team_stats(
                team_id
            )
        )

    return result


# -------------------------------------------------
# СТАРАЯ ФУНКЦИЯ
# -------------------------------------------------

def get_match_stats(match_id):

    if not match_id:
        raise Exception(
            "BBS: отсутствует ID матча"
        )

    data = _request(
        f"{BASE_URL}/stored/matches/{match_id}/stats"
    )

    return data.get(
        "data"
)
