from telegram_bot import send_message

async def check_football():
    await send_message(
        "⚽ <b>Тест футбольного модуля</b>\n\n"
        "✅ Бот проверил футбольные матчи.\n"
        "Пока это тестовое сообщение."
    )
