from telegram_bot import send_message
from odds_provider import get_odds_matches

from datetime import datetime
from zoneinfo import ZoneInfo


# =================================================
# ФОРМАТ ДАТЫ
# =================================================

def format_date(value):

    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        return dt.astimezone(
            ZoneInfo("Europe/Kyiv")
        ).strftime(
            "%d.%m.%Y %H:%M"
        )

    except Exception:
        return str(value)


# =================================================
# НАЗВАНИЕ ЛИГИ
# =================================================

def get_league_name(value):

    if isinstance(value, dict):

        return (
            value.get("name")
            or value.get("slug")
            or "—"
        )

    return str(value or "—")


# =================================================
# КОЭФФИЦИЕНТЫ
# =================================================

def format_odds(odds_data):

    if not isinstance(odds_data, dict):
        return "Коэффициенты не найдены."

    bookmakers = odds_data.get(
        "bookmakers",
        {}
    )

    if not isinstance(bookmakers, dict):
        return "Коэффициенты не найдены."

    lines = []

    for bookmaker, markets in bookmakers.items():

        if not isinstance(markets, list):
            continue

        lines.append(
            f"\n🏦 <b>{bookmaker}</b>"
        )

        for market in markets:

            if not isinstance(market, dict):
                continue

            market_name = market.get(
                "name",
                "—"
            )

            odds = market.get(
                "odds",
                []
            )

            if not isinstance(odds, list):
                continue

            for odd in odds:

                if not isinstance(odd, dict):
                    continue

                # П1 / X / П2
                if market_name in (
                    "ML",
                    "1X2",
                    "Moneyline"
                ):

                    home = odd.get(
                        "home"
                    )

                    draw = odd.get(
                        "draw"
                    )

                    away = odd.get(
                        "away"
                    )

                    if home is not None:
                        lines.append(
                            f"⚽ П1: <b>{home}</b>"
                        )

                    if draw is not None:
                        lines.append(
                            f"🤝 X: <b>{draw}</b>"
                        )

                    if away is not None:
                        lines.append(
                            f"⚽ П2: <b>{away}</b>"
                        )

                # Тотал
                elif market_name in (
                    "Totals",
                    "total",
                    "totals"
                ):

                    hdp = odd.get(
                        "hdp"
                    )

                    over = odd.get(
                        "over"
                    )

                    under = odd.get(
                        "under"
                    )

                    if hdp is not None:

                        if over is not None:
                            lines.append(
                                f"🔥 ТБ {hdp}: "
                                f"<b>{over}</b>"
                            )

                        if under is not None:
                            lines.append(
                                f"❄️ ТМ {hdp}: "
                                f"<b>{under}</b>"
                            )

    if not lines:
        return "Коэффициенты не найдены."

    return "\n".join(lines)


# =================================================
# ПРОВЕРКА ФУТБОЛА
# =================================================

async def check_football():

    try:

        # Получаем матчи вместе с коэффициентами
        matches = get_odds_matches(
            limit=20
        )

        await send_message(
            "⚽ <b>EDGEHUNTER AI</b>\n\n"
            f"Получено матчей с коэффициентами: "
            f"<b>{len(matches)}</b>"
        )

        # Пока выводим только первые 3
        # чтобы не заспамить Telegram
        for match in matches[:3]:

            if not isinstance(
                match,
                dict
            ):
                continue

            # ВАЖНО:
            # Odds-API.io отдаёт эти поля
            # непосредственно в match
            home = (
                match.get("home")
                or "—"
            )

            away = (
                match.get("away")
                or "—"
            )

            date = format_date(
                match.get("date")
            )

            league = get_league_name(
                match.get("league")
            )

            event_id = match.get(
                "id"
            )

            odds_data = match.get(
                "odds"
            )

            odds_text = format_odds(
                odds_data
            )

            text = (
                "🔎 <b>EDGEHUNTER AI</b>\n\n"

                f"🏆 <b>{league}</b>\n"

                f"⚽ <b>{home}</b> — "
                f"<b>{away}</b>\n"

                f"📅 <b>{date}</b>\n"

                f"🆔 {event_id}\n\n"

                f"💰 <b>КОЭФФИЦИЕНТЫ</b>\n"
                f"{odds_text}\n\n"

                "🧠 Пока тестируем получение "
                "коэффициентов."
            )

            await send_message(
                text
            )

    except Exception as e:

        await send_message(
            "❌ <b>FOOTBALL ERROR</b>\n\n"
            f"<code>{str(e)[:2000]}</code>"
        )
