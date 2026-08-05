from telegram_bot import send_message

already_sent = False

async def check_football():
    global already_sent

    if already_sent:
        return

    already_sent = True

    await send_message(
        "⚽ EdgeHunterAI\n\n"
        "✅ Футбольный модуль работает.\n"
        "Ожидаю реальные данные для анализа."
    )
