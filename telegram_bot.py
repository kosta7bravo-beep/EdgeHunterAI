from telegram import Bot
from config import BOT_TOKEN, CHAT_ID

bot = Bot(token=BOT_TOKEN)

async def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN или CHAT_ID не настроены.")
        return

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode="HTML"
    )
