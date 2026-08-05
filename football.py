from telegram_bot import send_message
from match_analyzer import analyze_match

already_sent = False

async def check_football():
    global already_sent

    if already_sent:
        return

    already_sent = True

    # Пока тестовый матч.
    # Позже вместо него будут реальные данные.
    match = {
        "league": "Premier League",
        "home": "Arsenal",
        "away": "Chelsea",
        "odd": 1.91,
        "home_form": 4,
        "away_form": 3,
        "goals_avg": 2.9
    }

    result = analyze_match(match)

    if result["score"] >= 80:
        await send_message(
            f"🟢 <b>STRONG SIGNAL</b>\n\n"
            f"⚽ {match['home']} — {match['away']}\n\n"
            f"📊 Оценка: {result['score']}/100\n\n"
            f"Причины:\n• " + "\n• ".join(result["reasons"])
                 )
