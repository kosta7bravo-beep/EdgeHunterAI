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
        f"⚽ <b>Анализирую {len(matches)} "
        f"реальных матчей...</b>"
    )

    signals = []

    for match in matches:

        try:
            result = analyze_match(match)

        except Exception as e:
            await send_message(
                f"⚠️ Ошибка анализа "
                f"{match.get('home', '?')} — "
                f"{match.get('away', '?')}:\n{e}"
            )
            continue

        if result.get("signal"):

            signals.append(
                (match, result)
            )

    # Нет подходящих сигналов
    if not signals:

        await send_message(
            "🔎 <b>EDGEHUNTER AI</b>\n\n"
            "Сегодня подходящих Value-сигналов "
            "не найдено.\n\n"
            "Это нормально — бот не будет "
            "придумывать ставку, если "
            "преимущества недостаточно."
        )

        return

    # Отправляем найденные сигналы
    for match, result in signals:

        home = match.get(
            "home",
            "?"
        )

        away = match.get(
            "away",
            "?"
        )

        league = match.get(
            "league",
            "?"
        )

        date = format_date(
            match.get("date")
        )

        probability = result.get(
            "probability"
        )

        value = result.get(
            "value"
        )

        odds = result.get(
            "odds"
        )

        bookmaker = result.get(
            "bookmaker",
            "—"
        )

        probability_text = (
            f"{probability:.1f}%"
            if probability is not None
            else "—"
        )

        value_text = (
            f"{value:+.2f}%"
            if value is not None
            else "—"
        )

        odds_text = (
            f"{odds:.3f}"
            if odds is not None
            else "—"
        )

        text = (
            "🔥 <b>EDGEHUNTER AI</b>\n\n"
            f"🏆 {league}\n"
            f"⚽ <b>{home} — {away}</b>\n"
            f"📅 {date}\n\n"

            f"🎯 <b>СТАВКА: "
            f"{result.get('bet', '—')}</b>\n\n"

            f"💰 Коэффициент: "
            f"<b>{odds_text}</b>\n"
            f"🏦 Букмекер: "
            f"<b>{bookmaker}</b>\n\n"

            f"📊 Рыночная вероятность: "
            f"{probability_text}\n"
            f"📈 Value: "
            f"<b>{value_text}</b>\n\n"

            "ℹ️ Это рыночный Value-сигнал. "
            "Статистика команд пока не подключена."
        )

        await send_message(text)
      
