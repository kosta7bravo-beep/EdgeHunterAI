from telegram_bot import send_message
from match_analyzer import analyze_match
from match_provider import get_matches

already_sent = False

async def check_football():
    global already_sent

    if already_sent:
        return

    already_sent = True

    matches = get_matches()

    for match in matches:

        result = analyze_match(match)

        if result["score"] >= 80:

            text = (
                "🟢 <b>STRONG SIGNAL</b>\n\n"
                f"⚽ {match['home']} — {match['away']}\n"
                f"🏆 {match['league']}\n\n"
                f"📊 Оценка: {result['score']}/100\n\n"
                "Причины:\n• "
                + "\n• ".join(result["reasons"])
            )

            await send_message(text)
