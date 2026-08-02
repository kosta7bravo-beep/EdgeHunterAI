import asyncio

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
            print(f"Ошибка: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
