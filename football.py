from telegram_bot import send_message
from match_analyzer import analyze_match
from match_provider import get_matches
from sent_storage import load_sent, save_sent


async def check_football():
    sent = load_sent()

    matches = get_matches()
    await send_message(f"⚽ Найдено матчей: {len(matches)}")

    for match in matches:

        match_id = f"{match['league']}_{match['home']}_{match['away']}"

        if match_id in sent:
            continue

        result = analyze_match(match)

        if result["score"] >= 80:

            text = (
                "🔥 <b>EDGEHUNTER AI</b>\n\n"
                "📅 Дата: скоро будет добавлена\n"
                "🕒 Время: скоро будет добавлено\n\n"
                f"🏆 {match['league']}\n"
                f"⚽ {match['home']} — {match['away']}\n\n"
                f"🎯 <b>СТАВКА:</b> {result['bet']}\n\n"
                f"📊 Вероятность: {result['probability']}%\n"
                f"💰 Рекомендуемый коэффициент: {result['odds']}\n\n"
                "📋 Причины:\n• "
                + "\n• ".join(result["reasons"])
            )

            await send_message(text)

            sent.append(match_id)

    save_sent(sent)
