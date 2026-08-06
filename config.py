import os

# ===== Telegram =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# ===== API Keys =====
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

# ===== Настройки =====
CHECK_INTERVAL = 900     # проверка каждые 5 минут
MIN_VALUE = 5             # минимальный Value (%)
MIN_ODDS = 1.50
MAX_ODDS = 5.00
