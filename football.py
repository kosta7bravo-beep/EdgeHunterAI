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
        f"🔎 <b>BETWAY DIAGNOSTIC</b>\n\n"
        f"Найдено матчей: {len(matches)}"
    )

    for index, match in enumerate(matches[:3], 1):

        home = match.get("home", "?")
        away = match.get("away", "?")
        league = match.get("league", "?")
        date = format_date(match.get("date"))

        bookmakers = match.get(
            "odds_data",
            {}
        )

        betway = bookmakers.get("Betway")

        text = (
            f"🔎 <b>{index}. "
            f"{home} — {away}</b>\n"
            f"🏆 {league}\n"
            f"📅 {date}\n\n"
        )

        if not betway:
            text += "❌ Betway: данных нет\n"
            await send_message(text)
            continue

        if isinstance(betway, dict):
            markets = list(betway.values())
        elif isinstance(betway, list):
            markets = betway
        else:
            text += (
                f"⚠️ Неизвестный формат Betway:\n"
                f"{betway}\n"
            )
            await send_message(text)
            continue

        text += "💰 <b>РЫНКИ BETWAY:</b>\n"

        found = False

        for market in markets:

            if not isinstance(market, dict):
                continue

            name = (
                market.get("name")
                or market.get("market")
                or market.get("key")
                or "Без названия"
            )

            text += f"• {name}\n"
            found = True

        if not found:
            text += "❌ Названия рынков не найдены\n"

        await send_message(text)
