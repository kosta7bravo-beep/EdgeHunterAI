def implied_probability(odds):
    """Перевод коэффициента в имплайд-вероятность."""

    if not odds or odds <= 1:
        return None

    return 1 / odds


def value_percent(probability, odds):
    """Расчёт математического Value."""

    if probability is None or not odds or odds <= 1:
        return None

    return (probability * odds - 1) * 100


def get_best_odds(bookmakers):
    """
    Ищет лучшие коэффициенты среди Bet365 и Betway.
    """

    result = {
        "home": [],
        "draw": [],
        "away": [],
        "over_2_5": [],
        "under_2_5": [],
        "btts_yes": [],
        "btts_no": []
    }

    for bookmaker_name in ("Bet365", "Betway"):

        markets = bookmakers.get(bookmaker_name, [])

        if isinstance(markets, dict):
            markets = list(markets.values())

        if not isinstance(markets, list):
            continue

        for market in markets:

            if not isinstance(market, dict):
                continue

            name = (
                market.get("name")
                or market.get("market")
                or market.get("key")
            )

            odds_list = market.get("odds", [])

            if isinstance(odds_list, dict):
                odds_list = [odds_list]

            if not isinstance(odds_list, list):
                continue

            # -------------------------
            # 1X2
            # -------------------------

            if name == "ML":

                for odd in odds_list:

                    if not isinstance(odd, dict):
                        continue

                    home = odd.get("home")
                    draw = odd.get("draw")
                    away = odd.get("away")

                    if home:
                        result["home"].append(
                            (bookmaker_name, float(home))
                        )

                    if draw:
                        result["draw"].append(
                            (bookmaker_name, float(draw))
                        )

                    if away:
                        result["away"].append(
                            (bookmaker_name, float(away))
                        )

            # -------------------------
            # Totals
            # -------------------------

            elif name == "Totals":

                for odd in odds_list:

                    if not isinstance(odd, dict):
                        continue

                    line = (
                        odd.get("hdp")
                        or odd.get("line")
                        or odd.get("total")
                    )

                    if line != 2.5:
                        continue

                    over = odd.get("over")
                    under = odd.get("under")

                    if over:
                        result["over_2_5"].append(
                            (bookmaker_name, float(over))
                        )

                    if under:
                        result["under_2_5"].append(
                            (bookmaker_name, float(under))
                        )

            # -------------------------
            # Both Teams To Score
            # -------------------------

            elif name == "Both Teams To Score":

                for odd in odds_list:

                    if not isinstance(odd, dict):
                        continue

                    yes = (
                        odd.get("yes")
                        or odd.get("Yes")
                    )

                    no = (
                        odd.get("no")
                        or odd.get("No")
                    )

                    if yes:
                        result["btts_yes"].append(
                            (bookmaker_name, float(yes))
                        )

                    if no:
                        result["btts_no"].append(
                            (bookmaker_name, float(no))
                        )

    return result


def best_price(values):
    """Возвращает лучший коэффициент и букмекера."""

    if not values:
        return None, None

    bookmaker, odds = max(
        values,
        key=lambda item: item[1]
    )

    return odds, bookmaker


def analyze_match(match):

    bookmakers = match.get(
        "odds_data",
        {}
    )

    odds = get_best_odds(bookmakers)

    candidates = []

    markets = [
        ("Победа хозяев", odds["home"]),
        ("Ничья", odds["draw"]),
        ("Победа гостей", odds["away"]),
        ("ТБ 2.5", odds["over_2_5"]),
        ("ТМ 2.5", odds["under_2_5"]),
        ("Обе забьют — Да", odds["btts_yes"]),
        ("Обе забьют — Нет", odds["btts_no"])
    ]

    for bet_name, prices in markets:

        if len(prices) < 1:
            continue

        best_odds, bookmaker = best_price(prices)

        if not best_odds:
            continue

        # Используем среднюю имплайд-вероятность
        # доступных букмекеров.
        probabilities = []

        for _, price in prices:

            probability = implied_probability(price)

            if probability:
                probabilities.append(probability)

        if not probabilities:
            continue

        average_probability = (
            sum(probabilities)
            / len(probabilities)
        )

        value = value_percent(
            average_probability,
            best_odds
        )

        if value is None:
            continue

        candidates.append({
            "bet": bet_name,
            "odds": best_odds,
            "bookmaker": bookmaker,
            "probability": average_probability * 100,
            "value": value
        })

    if not candidates:

        return {
            "score": 0,
            "bet": None,
            "odds": None,
            "probability": None,
            "value": None,
            "bookmaker": None,
            "reasons": [
                "Недостаточно данных для анализа"
            ]
        }

    # Выбираем максимальный Value.
    best = max(
        candidates,
        key=lambda item: item["value"]
    )

    # Пока строгий фильтр.
    # Никаких сигналов при небольшом преимуществе.
    if best["value"] < 5:

        return {
            "score": 0,
            "bet": None,
            "odds": best["odds"],
            "probability": best["probability"],
            "value": best["value"],
            "bookmaker": best["bookmaker"],
            "reasons": [
                "Value ниже минимального порога"
            ]
        }

    # Условный технический score.
    # Это НЕ вероятность выигрыша.
    score = min(
        95,
        max(
            0,
            round(50 + best["value"] * 2)
        )
    )

    reasons = [
        "Есть положительное Value",
        f"Лучший коэффициент: {best['bookmaker']}",
        f"Value: {best['value']:.2f}%"
    ]

    return {
        "score": score,
        "bet": best["bet"],
        "odds": best["odds"],
        "probability": best["probability"],
        "value": best["value"],
        "bookmaker": best["bookmaker"],
        "reasons": reasons
            }
