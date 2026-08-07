TOP_LEAGUES = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Champions League",
    "Europa League",
    "Украина Премьер-лига"
]


def analyze_match(match):
    score = 0
    reasons = []

    if match.get("league") in TOP_LEAGUES:
        score += 20
        reasons.append("Топ-лига")

    if match.get("home_form", 0) >= 3:
        score += 20
        reasons.append("Хорошая форма хозяев")

    if match.get("away_form", 0) >= 3:
        score += 20
        reasons.append("Хорошая форма гостей")

    if match.get("goals_avg", 0) >= 2.5:
        score += 20
        reasons.append("Высокая результативность")

    odd = match.get("odd", 1.80)

    if match.get("goals_avg", 0) >= 2.8:
        bet = "ТБ 2.5"
    elif match.get("home_form", 0) > match.get("away_form", 0):
        bet = "Победа хозяев"
    elif match.get("away_form", 0) > match.get("home_form", 0):
        bet = "Победа гостей"
    else:
        bet = "Обе забьют — Да"

    probability = min(score, 95)

    return {
        "score": score,
        "bet": bet,
        "probability": probability,
        "odds": f"{odd:.2f}",
        "reasons": reasons
    }
