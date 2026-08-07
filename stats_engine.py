from dataclasses import dataclass


@dataclass
class MatchStatistics:

    home_form = 0
    away_form = 0

    home_attack = 0
    away_attack = 0

    home_defence = 0
    away_defence = 0

    home_xg = 0
    away_xg = 0

    home_goals = 0
    away_goals = 0

    home_shots = 0
    away_shots = 0

    motivation = 0

    injuries = 0

    h2h = 0


def build_statistics(match):

    stats = MatchStatistics()

    return stats
