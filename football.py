from datetime import datetime

from telegram_bot import send_message
from match_provider import get_matches
from match_analyzer import analyze_match


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


def get_odds(market):
    if not market:
        return []

    odds = market.get("odds", [])

    if isinstance(odds, dict):
        odds = [odds]

    return odds if isinstance(odds, list) else []


def format_ml(markets):
    market = get_market(markets, "ML")

    if not market:
        return "нет данных"

    odds = get_odds(market)

    if not odds:
        return "нет данных"

    odd = odds[0]

    return (
        f"П1: {odd.get('home', '—')} | "
        f"X: {odd.get('draw', '—')} | "
        f"П2: {odd.get('away', '—')}"
    )


def format_totals_25(markets):
    market = get_market(markets, "Totals")

    if not market:
        return "нет данных"

    odds = get_odds(market)

    for odd in odds:

        if not isinstance(odd, dict):
            continue

        line = (
            odd.get("hdp")
            or odd.get("line")
            or odd.get("total")
        )

        try:
            if float(line) != 2.5:
                continue
        except (TypeError, ValueError):
            continue

        return (
            f"ТБ 2.5: {odd.get('over', '—')} | "
            f"ТМ 2.5: {odd.get('under', '—')}"
        )

    return "линия 2.5 не найдена"


def format_btts(markets):
    market = get_market(
        markets,
        "Both Teams To Score"
    )

    if not market:
        return "нет данных"

    odds = get_odds(market)

    if not odds:
        return "нет данных"

    odd = odds[0]

    yes = odd.get("yes") or odd.get("Yes")
    no = odd.get("no") or odd.get("No")

    if yes is None:
        yes = odd.get("home")

    if no is None:
        no = odd.get("away")

    return (
        f"Да: {yes if yes is not None else '—'} | "
        f"Нет: {no if no is not None else '—'}"
    )


def format_bookmaker(name, markets):
    text = f"💰 <b>{name}</b>\n"

    text += (
        "🏆 1X2\n"
        f"{format_ml(markets)}\n"
    )

    text += (
        "⚽ ТБ/ТМ 2.5\n"
        f"{format_totals_25(markets)}\n"
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

        home = match.get("home", "?")
        away = match.get("away", "?")
        league = match.get("league", "?")
        date = format_date(match.get("date"))

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
                text += (
                    f"💰 <b>{bookmaker_name}</b>\n"
                    "❌ данных нет\n\n"
                )
                continue

            if isinstance(markets, dict):
                markets = list(markets.values())

            if not isinstance(markets, list):
                text += (
                    f"💰 <b>{bookmaker_name}</b>\n"
                    "❌ неизвестный формат данных\n\n"
                )
                continue

            text += format_bookmaker(
                bookmaker_name,
                markets
            )

            text += "\n"

        # Пока просто показываем реальные данные.
        # Прогнозы подключим после проверки.
        if len(text) > 3800:
            await send_message(text[:3800])
        else:
            await send_message(text)
