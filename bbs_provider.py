import os
import time
import requests


BASE_URL = "https://api.bigballsdata.com/v1"

BBS_API_KEY = os.environ.get("BBS_API_KEY", "").strip()

CACHE_TIME = 1800

_matches_cache = None
_matches_cache_time = 0


def _headers():
    if not BBS_API_KEY:
        raise Exception(
            "BBS_API_KEY не указан в переменных окружения"
        )

    return {
        "Authorization": f"Bearer {BBS_API_KEY}"
    }


def _request(url, params=None):
    response = requests.get(
        url,
        headers=_headers(),
        params=params or {},
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"BBS API STATUS {response.status_code}: "
            f"{response.text[:500]}"
        )

    data = response.json()

    if data.get("error"):
        raise Exception(
            f"BBS API ERROR: {data['error']}"
        )

    return data


def get_matches(limit=100):
    """
    Получает ближайшие футбольные матчи.
    Результат кэшируется, чтобы не тратить запросы
    каждые 15 минут.
    """

    global _matches_cache
    global _matches_cache_time

    now = time.time()

    if (
        _matches_cache is not None
        and now - _matches_cache_time < CACHE_TIME
    ):
        return _matches_cache

    data = _request(
        f"{BASE_URL}/matches",
        {
            "sport": "football",
            "limit": limit
        }
    )

    matches = data.get("data", [])

    if not isinstance(matches, list):
        raise Exception(
            f"Неожиданный BBS ответ matches: {data}"
        )

    _matches_cache = matches
    _matches_cache_time = now

    return matches


def _team_name(team):
    """
    Приводит разные варианты структуры команды
    к обычной строке.
    """

    if isinstance(team, str):
        return team

    if isinstance(team, dict):
        return (
            team.get("name")
            or team.get("short_name")
            or team.get("display_name")
            or ""
        )

    return ""


def find_match(home, away):
    """
    Ищет матч Big Balls по названиям команд.
    """

    home = home.lower().strip()
    away = away.lower().strip()

    matches = get_matches()

    for match in matches:

        match_home = _team_name(
            match.get("home")
        ).lower().strip()

        match_away = _team_name(
            match.get("away")
        ).lower().strip()

        if (
            home in match_home
            or match_home in home
        ) and (
            away in match_away
            or match_away in away
        ):
            return match

    return None


def get_match_stats(match_id):
    """
    Получает статистику конкретного матча.
    """

    if not match_id:
        return None

    data = _request(
        f"{BASE_URL}/stored/matches/{match_id}/stats"
    )

    stats = data.get("data")

    return stats


def get_stats_for_match(home, away):
    """
    Удобная функция:
    1. ищет матч;
    2. получает его ID;
    3. получает статистику.
    """

    match = find_match(home, away)

    if not match:
        return {
            "found": False,
            "match": None,
            "stats": None
        }

    match_id = match.get("id")

    if not match_id:
        return {
            "found": True,
            "match": match,
            "stats": None
        }

    stats = get_match_stats(match_id)

    return {
        "found": True,
        "match": match,
        "stats": stats
      }
