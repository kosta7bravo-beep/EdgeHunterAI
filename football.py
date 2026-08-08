from datetime import datetime

from telegram_bot import send_message
from match_provider import get_matches


def format_date(date_string):
    if not date_string:
        return "—"

    try:
        dt = datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        )
        return dt.strftime("%d.%m.%Y %H:%M UTC")
    except Exception:
        return str(date_string)


def get_market(markets, market_name):
    """
    Находит конкретный рынок.
    """

    for market in markets:

        if not isinstance(market, dict):
            continue

        name = (
            market.get("name")
            or market.get("market")
            or market.get("key")
        )

        if name == market_name:
            return market

    return None


def get_market_odds(market):
    """
    Возвращает список коэффициентов рынка.
    """

    if not market:
        return []

    odds = market.get("odds", [])

    if isinstance(odds, dict):
        odds = [odds]

    if not isinstance(odds, list):
        return []

    return odds


def format_ml(markets):
    """
    П1 / X / П2
    """

    market = get_market(markets, "ML")

    if not market:
        return "нет данных"

    odds = get_market_odds(market)

    if not odds:
        return "нет данных"

    odd = odds[0]

    home = odd.get("home", "—")
    draw = odd.get("draw", "—")
    away = odd.get("away", "—")

    return (
        f"П1: {home} | "
        f"X: {draw} | "
        f"П2: {away}"
    )


def format_totals(markets):
    """
    Показываем все основные линии тотала.
    Это временно нужно для определения ТБ/ТМ 2.5.
    """

    market = get_market(markets, "Totals")

    if not market:
        return "нет данных"

    odds = get_market_odds(market)

    if not odds:
        return "нет данных"

    result = []

    for odd in odds:

        if not isinstance(odd, dict):
            continue

        over = odd.get("over")
        under = odd.get("under")
        line = (
            odd.get("hdp")
            or odd.get("line")
            or odd.get("total")
        )

        if over is None and under is None:
            continue

        result.append(
            f"{line}: ТБ {over} / ТМ {under}"
        )

    if not result:
        return "нет данных"

    return "\n".join(result)


def format_btts(markets):
    """
    Обе забьют — Да / Нет.
    """

    market = get_market(
        markets,
        "Both Teams To Score"
    )

    if not market:
        return "нет данных"

    odds = get_market_odds(market)

    if not odds:
        return "нет данных"

    odd = odds[0]

    yes = (
        odd.get("yes")
        or odd.get("Yes")
        or odd.get("home")
    )

    no = (
        odd.get("no")
        or odd.get("No")
        or odd.get("away")
    )

    return (
        f"Да: {yes or '—'} | "
        f"Нет: {no or '—'}"
    )


def format_bookmaker(bookmaker_name, markets):

    text = (
        f"💰 <b>{bookmaker_name}</b>\n"
    )

    text += (
        "🏆 1X2\n"
        f"{format_ml(markets)}\n\n"
    )

    text += (
        "⚽ Тоталы\n"
        f"{format_totals(markets)}\n\n"
    )

    text += (
        "🎯 Обе забьют\n"
        f"{format_btts(markets)}\n"
    )

    return text


async def check_football():

    try:
        matches = get_matches()

    except Exception as e:

        await send_message(
            f"⚠️ <b>MATCH_PROVIDER</b>\n{e}"
        )

        return

    if not matches:

        await send_message(
            "⚽ Матчей сейчас не найдено."
        )

        return

    await send_message(
        f"⚽ <b>Найдено реальных матчей: "
        f"{len(matches)}</b>"
    )

    for index, match in enumerate(matches, 1):

        league = (
            match.get("league")
            or "Неизвестная лига"
        )

        home = (
            match.get("home")
            or "?"
        )

        away = (
            match.get("away")
            or "?"
        )

        date = format_date(
            match.get("date")
        )

        bookmakers = match.get(
            "odds_data",
            {}
        )

        text = (
            f"⚽ <b>{index}. "
            f"{home} — {away}</b>\n"
            f"🏆 {league}\n"
            f"📅 {date}\n\n"
        )

        for bookmaker_name in (
            "Bet365",
            "Betway"
        ):

            markets = bookmakers.get(
                bookmaker_name
            )

            if markets is None:
                continue

            if isinstance(markets, dict):
                markets = list(
                    markets.values()
                )

            if not isinstance(markets, list):
                continue

            text += format_bookmaker(
                bookmaker_name,
                markets
            )

            text += "\n\n"

        # Telegram ограничивает длину сообщения
        if len(text) > 3800:

            await send_message(
                text[:3800]
            )

        else:

            await send_message(text)
