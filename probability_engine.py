from dataclasses import dataclass


@dataclass
class TeamStats:
    home_form: float = 0
    away_form: float = 0
    attack: float = 0
    defence: float = 0
    xg: float = 0
    goals_avg: float = 0
    h2h: float = 0
    injuries: float = 0
    motivation: float = 0


def calculate_probability(home: TeamStats, away: TeamStats):

    home_score = (
        home.home_form * 0.20 +
        home.attack * 0.20 +
        home.defence * 0.15 +
        home.xg * 0.15 +
        home.goals_avg * 0.10 +
        home.h2h * 0.10 +
        home.motivation * 0.10
    )

    away_score = (
        away.away_form * 0.20 +
        away.attack * 0.20 +
        away.defence * 0.15 +
        away.xg * 0.15 +
        away.goals_avg * 0.10 +
        away.h2h * 0.10 +
        away.motivation * 0.10
    )

    total = home_score + away_score

    if total == 0:
        return {
            "home": 33,
            "draw": 34,
            "away": 33
        }

    home_probability = round(home_score / total * 100)

    away_probability = round(away_score / total * 100)

    draw_probability = max(0, 100 - home_probability - away_probability)

    return {
        "home": home_probability,
        "draw": draw_probability,
        "away": away_probability
  }
