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

    # Лига
    if match.get("league") in TOP_LEAGUES:
        score += 20
        reasons.append("Топ-лига")

    # Коэффициент
    odd = match.get("odd", 0)

    if 1.70 <= odd <= 2.40:
        score += 20
        reasons.append("Хороший коэффициент")

    # Домашняя форма
    if match.get("home_form", 0) >= 3:
        score += 20
        reasons.append("Хорошая форма хозяев")

    # Гостевая форма
    if match.get("away_form", 0) >= 3:
        score += 20
        reasons.append("Хорошая форма гостей")

    # Средняя результативность
    if match.get("goals_avg", 0) >= 2.5:
        score += 20
        reasons.append("Высокая результативность")

    return {
        "score": score,
        "reasons": reasons
  }
