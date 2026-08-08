from datetime import datetime, timezone

from telegram_bot import send_message
from match_provider import get_matches


def format_date(date_string):
    if not date_string:
        return "—"

    try:
        dt = datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        )

        # Показываем время по UTC
        return dt.strftime("%d.%m.%Y %H:%M UTC")

    except Exception:
        return str(date_string)


def format_odds(bookmakers):
    """
    Показывает полученные от API коэффициенты.
    Мы пока не предполагаем конкретную структуру рынка,
    а выводим доступные данные безопасно.
    """

    if not bookmakers:
        return "❌ Коэффициенты не получены"

    text = ""

    for bookmaker_name, markets in bookmakers.items():

        text += f"\n💰 <b>{bookmaker_name}</b>\n"

        if not markets:
            text += "Нет рынков\n"
            continue

        if isinstance(markets, dict):
            markets = [markets]

        if not isinstance(markets, list):
            text += f"{markets}\n"
            continue

        for market in markets:

            if not isinstance(market, dict):
                continue

            market_name = (
                market.get("name")
                or market.get("market")
                or market.get("key")
                or "Рынок"
            )

            text += f"  📊 {market_name}\n"

            odds = market.get("odds", [])

            if isinstance(odds, dict):
                odds = [odds]

            if isinstance(odds, list):

                for odd in odds:

                    if not isinstance(odd, dict):
                        continue

                    # Пытаемся показать основные значения
                    values = []

                    for key, value in odd.items():

                        if key in (
                            "home",
                            "draw",
                            "away",
                            "over",
                            "under",
                            "price",
                            "odds"
                        ):
                            values.append(
                                f"{key}: {value}"
                            )

                    if values:
                        text += (
                            "    "
                            + " | ".join(values)
                            + "\n"
                        )

            else:
                text += f"    {odds}\n"

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

    # Один общий Telegram-пакет,
    # чтобы не отправлять 10 отдельных сообщений
    text = "⚽ <b>EDGEHUNTER AI — РЕАЛЬНЫЕ МАТЧИ</b>\n\n"

    for index, match in enumerate(matches, 1):

        league = match.get("league") or "Неизвестная лига"
        home = match.get("home") or "?"
        away = match.get("away") or "?"
        date = format_date(match.get("date"))

        text += (
            f"<b>{index}. {home} — {away}</b>\n"
            f"🏆 {league}\n"
            f"📅 {date}\n"
        )

        bookmakers = match.get(
            "odds_data",
            {}
        )

        text += format_odds(bookmakers)

        text += "\n"

    # Telegram имеет ограничение на размер сообщения.
    # Если вдруг данных слишком много — отправляем частями.
    max_length = 3800

    if len(text) <= max_length:

        await send_message(text)

    else:

        current = ""

        for line in text.splitlines(True):

            if len(current) + len(line) > max_length:

                if current:
                    await send_message(current)

                current = line

            else:
                current += line

        if current:
            await send_message(current)
