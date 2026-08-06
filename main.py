import asyncio
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "EdgeHunterAI is running"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web, daemon=True).start()
from football import check_football
from crypto import check_crypto
from live import check_live
from telegram_bot import send_message
from config import CHECK_INTERVAL


async def main():
    await send_message("✅ <b>EdgeHunterAI запущен!</b>")

    while True:
        try:
            await check_football()
            await check_live()
            await check_crypto()

        except Exception as e:
    await send_message(f"❌ Ошибка:\n{e}")

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
