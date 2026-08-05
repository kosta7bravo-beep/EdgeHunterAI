import json
import os

FILE_NAME = "sent_matches.json"


def load_sent():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sent(matches):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False)
