import json
import os

SENT_FILE = "sent_matches.json"


def load_sent_matches():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_sent_matches(sent):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent), f, ensure_ascii=False)


async def check_football():
    sent = load_sent_matches()

    # Пока список тестовый.
    # Позже сюда будут поступать реальные матчи.
    matches = [
        {
            "id": "test_1",
            "league": "Premier League",
            "home": "Arsenal",
            "away": "Chelsea",
            "bet": "ТБ 2.5",
            "odd": 1.91,
            "confidence": 84,
        }
    ]

    for match in matches:
        if match["id"] in sent:
            continue

        print(
            f"⚽ Новый сигнал: "
            f"{match['home']} - {match['away']} "
            f"{match['bet']}"
        )

        sent.add(match["id"])

    save_sent_matches(sent)
