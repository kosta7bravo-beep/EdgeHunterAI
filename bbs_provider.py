import os
import time
import requests
from datetime import datetime, timezone, timedelta


BASE_URL = "https://api.bigballsdata.com/v1"

BBS_API_KEY = os.environ.get("BBS_API_KEY", "").strip()
def check_bbs_coverage():

    data = _request(
        f"{BASE_URL}/coverage",
        {
            "sport": "football"
        }
    )

    return data
# -------------------------------------------------
# НАСТРОЙКИ
# -------------------------------------------------

# Как часто обновлять список матчей
MATCHES_CACHE_TIME = 1800  # 30 минут

# Как долго хранить статистику команд
TEAM_CACHE_TIME = 21600  # 6 часов

# На сколько дней вперед ищем матчи
MATCHES_DAYS_AHEAD = 180

# Сколько матчей запрашиваем у BBS
API_MATCH_LIMIT = 200

# -------------------------------------------------
# CACHE
# -------------------------------------------------

_cached_matches = None
_cached_matches_time = 0

_team_cache = {}


# -------------------------------------------------
# HEADERS
# -------------------------------------------------

def _headers():

    if not BBS_API_KEY:
        raise Exception(
            "BBS_API_KEY не найден в Environment"
        )

    return {
        "Authorization": "Bearer " + BBS_API_KEY,
        "Accept": "application/json",
    }


# -------------------------------------------------
# REQUEST
# -------------------------------------------------

def _request(url, params=None):

    try:

        response = requests.get(
            url,
            headers=_headers(),
            params=params or {},
            timeout=30
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
# ДАТА МАТЧА
# -------------------------------------------------

def _get_match_datetime(match):

    if not isinstance(match, dict):
        return None

    date_string = (
        match.get("kickoff_utc")
        or match.get("date")
        or match.get("start_time")
        or match.get("commence_time")
    )

    if not date_string:
        return None

    try:

        value = str(date_string).strip()

        # ISO UTC
        value = value.replace(
            "Z",
            "+00:00"
        )

        match_date = datetime.fromisoformat(
            value
        )

        if match_date.tzinfo is None:

            match_date = match_date.replace(
                tzinfo=timezone.utc
            )

        return match_date.astimezone(
            timezone.utc
        )

    except Exception:

        return None


# -------------------------------------------------
# НАЗВАНИЕ КОМАНДЫ
# -------------------------------------------------

def _team_name(value):

    if isinstance(value, dict):

        return (
            value.get("name")
            or value.get("short_name")
            or value.get("abbr")
            or ""
        )

    return str(value or "")


# -------------------------------------------------
# НОРМАЛИЗАЦИЯ МАТЧА
# -------------------------------------------------

def _normalize_match(match):

    if not isinstance(match, dict):
        return match

    result = dict(match)

    # BBS в разных ответах может отдавать
    # home/away как строку или объект.
    result["home"] = _team_name(
        match.get("home")
    )

    result["away"] = _team_name(
        match.get("away")
    )

    # Если используется другой формат команды
    if not result["home"]:

        result["home"] = _team_name(
            match.get("home_team")
        )

    if not result["away"]:

        result["away"] = _team_name(
            match.get("away_team")
        )

    # Приводим дату к единому полю
    match_date = _get_match_datetime(
        match
    )

    if match_date:

        result["kickoff_utc"] = (
            match_date.isoformat()
        )

    return result


# -------------------------------------------------
# ПОЛУЧЕНИЕ БЛИЖАЙШИХ МАТЧЕЙ
# -------------------------------------------------

def get_matches(limit=50):

    global _cached_matches
    global _cached_matches_time

    now_timestamp = time.time()

    # CACHE — один запрос максимум раз в 30 минут
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

    # Пока тестируем только Bundesliga.
    # BBS coverage показывает именно такой пример запроса.
    data = _request(
        f"{BASE_URL}/matches",
        {
            "sport": "football",
            "league": "bundesliga",
            "status": "scheduled",
            "limit": API_MATCH_LIMIT,
            "offset": 0
        }
    )

    matches = data.get(
        "data",
        []
    )
    print("BBS RAW RESPONSE:", data)
    if not isinstance(matches, list):
        raise Exception(
            "BBS: поле data не является списком"
        )

    filtered_matches = []

    for match in matches:

        match_date = _get_match_datetime(
            match
        )

        if not match_date:
            continue

        if match_date < now:
            continue

        if match_date > max_date:
            continue

        normalized = _normalize_match(
            match
        )

        filtered_matches.append(
            (
                match_date,
                normalized
            )
        )

    filtered_matches.sort(
        key=lambda item: item[0]
    )

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

        if (
            time.time()
            - cached["time"]
            < TEAM_CACHE_TIME
        ):

            return cached.get(
                "team"
            )

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

    if not isinstance(
        teams,
        list
    ):

        teams = []

    team = None

    # Точное совпадение
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

    # Если точного совпадения нет
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
        return []

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
# АНАЛИЗ ДВУХ КОМАНД
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
# СТАТИСТИКА КОНКРЕТНОГО МАТЧА
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
