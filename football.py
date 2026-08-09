from datetime import datetime, timezone

from telegram_bot import send_message
from odds_provider import get_odds_matches


MIN_VALUE = 5
MIN_ODDS = 1.50
MAX_ODDS = 5.00


def fair_odds(probability):

    if probability <= 0:
        return None

    return 1 / probability


def calculate_value(probability, odds):

    return (
        probability * odds - 1
    ) * 100


def parse_probability_from_odds(odds):

    if not odds or odds <= 0:
        return 0

    return 1 / odds


def format_date(value):

    if not value:
        return "—"

    try:

        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return dt.astimezone(
            timezone.utc
        ).strftime(
            "%d.%m.%Y %H:%M UTC"
        )

    except Exception:

        return str(value)


def extract_h2h(bookmakers):

    results = []

    for bookmaker in bookmakers or []:

        markets = bookmaker.get(
            "markets",
            []
        )

        for market in markets:

            if market.get("key") != "h2h":
                continue

            outcomes = market.get(
                "outcomes",
                []
            )

            for outcome in outcomes:

                name = outcome.get("name")
                price = outcome.get("price")

                if not name or not price:
                    continue

                results.append(
                    {
                        "name": name,
                        "odds": float(price),
                        "bookmaker": bookmaker.get(
                            "title",
                            "—"
                        )
                    }
                )

    return results


def extract_totals(bookmakers):

    results = []

    for bookmaker in bookmakers or []:

        markets = bookmaker.get(
            "markets",
            []
        )

        for market in markets:

            if market.get("key") != "totals":
                continue

            outcomes = market.get(
                "outcomes",
                []
            )

            for outcome in outcomes:

                name = outcome.get("name")
                point = outcome.get("point")
                price = outcome.get("price")

                if (
                    not name
                    or point is None
                    or not price
                ):
                    continue

                results.append(
                    {
                        "name": name,
                        "point": float(point),
                        "odds": float(price),
                        "bookmaker": bookmaker.get(
                            "title",
                            "—"
                        )
                    }
                )

    return results


async def check_football():

    try:

        matches = get_odds_matches()

        await send_message(
            "⚽ <b>EDGEHUNTER AI</b>\n\n"
            f"Получено матчей с коэффициентами: "
            f"<b>{len(matches)}</b>"
        )

        # Берём только ближайшие 3 матча
        matches = sorted(
            matches,
            key=lambda x: x.get(
                "commence_time",
                ""
            )
        )[:3]

        for match in matches:

            home = match.get(
                "home_team",
                "—"
            )

            away = match.get(
                "away_team",
                "—"
            )

            kickoff = format_date(
                match.get(
                    "commence_time"
                )
            )

            bookmakers = match.get(
                "bookmakers",
                []
            )

            h2h = extract_h2h(
                bookmakers
            )

            totals = extract_totals(
                bookmakers
            )

            text = (
                "🔎 <b>EDGEHUNTER AI</b>\n\n"
                f"⚽ <b>{home}</b> — "
                f"<b>{away}</b>\n"
                f"📅 {kickoff}\n\n"
            )

            if h2h:

                text += (
                    "🏆 <b>1X2</b>\n"
                )

                for item in h2h[:6]:

                    odds = item["odds"]

                    if (
                        MIN_ODDS
                        <= odds
                        <= MAX_ODDS
                    ):

                        text += (
                            f"{item['name']}: "
                            f"<b>{odds:.2f}</b>\n"
                        )

                text += "\n"

            if totals:

                text += (
                    "🔥 <b>ТОТАЛЫ</b>\n"
                )

                for item in totals[:6]:

                    odds = item["odds"]

                    if (
                        MIN_ODDS
                        <= odds
                        <= MAX_ODDS
                    ):

                        text += (
                            f"{item['name']} "
                            f"{item['point']:.1f}: "
                            f"<b>{odds:.2f}</b>\n"
                        )

                text += "\n"

            text += (
                "🧠 <b>Пока тестируем получение "
                "коэффициентов.</b>"
            )

            await send_message(
                text
            )

    except Exception as e:

        await send_message(
            "❌ <b>ODDS API ERROR</b>\n\n"
            f"<code>{str(e)[:1500]}</code>"
    )
      
