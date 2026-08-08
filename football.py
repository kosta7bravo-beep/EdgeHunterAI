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
            "⚽ Матчей не найдено."
        )
        return

    await send_message(
        f"🔎 <b>ДИАГНОСТИКА TOTALS</b>\n"
        f"Найдено матчей: {len(matches)}"
    )

    # Проверяем первые 3 матча.
    for index, match in enumerate(matches[:3], 1):

        home = match.get("home", "?")
        away = match.get("away", "?")
        league = match.get("league", "?")
        date = format_date(match.get("date"))

        bookmakers = match.get(
            "odds_data",
            {}
        )

        text = (
            f"🔎 <b>{index}. "
            f"{home} — {away}</b>\n"
            f"🏆 {league}\n"
            f"📅 {date}\n\n"
        )

        bet365 = bookmakers.get("Bet365")

        if not bet365:
            text += "❌ Bet365: данных нет\n"
            await send_message(text)
            continue

        if isinstance(bet365, dict):
            markets = list(bet365.values())
        elif isinstance(bet365, list):
            markets = bet365
        else:
            text += "❌ Неизвестный формат Bet365\n"
            await send_message(text)
            continue

        totals_found = False

        text += "⚽ <b>СЫРЫЕ TOTALS BET365:</b>\n\n"

        for market in markets:

            if not isinstance(market, dict):
                continue

            name = (
                market.get("name")
                or market.get("market")
                or market.get("key")
                or ""
            )

            if name.lower() != "totals":
                continue

            totals_found = True

            text += (
                f"Название рынка: {name}\n"
                f"Все поля рынка:\n"
                f"{market}\n\n"
            )

        if not totals_found:
            text += "❌ Рынок Totals не найден\n"

        # Telegram ограничение
        if len(text) > 3800:
            text = text[:3800]

        await send_message(text)
      
