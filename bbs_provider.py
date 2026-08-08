import os
import time
import requests


BASE_URL = "https://api.bigballsdata.com/v1"

BBS_API_KEY = os.environ.get("BBS_API_KEY", "").strip()

CACHE_TIME = 1800

_cached_matches = None
_cached_time = 0


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


def get_matches(limit=3):

    global _cached_matches
    global _cached_time

    now = time.time()

    if (
        _cached_matches is not None
        and now - _cached_time < CACHE_TIME
    ):
        return _cached_matches

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
            "BBS: поле data не является списком"
        )

    _cached_matches = matches
    _cached_time = now

    return matches


def get_match_stats(match_id):

    if not match_id:
        raise Exception(
            "BBS: отсутствует ID матча"
        )

    data = _request(
        f"{BASE_URL}/stored/matches/{match_id}/stats"
    )

    return data.get("data")
