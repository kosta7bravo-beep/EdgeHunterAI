def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def implied_probability(odds):
    odds = to_float(odds)

    if not odds or odds <= 1:
        return None

    return 1 / odds


def get_best_price(prices):
    """
    prices:
        [
            ("Bet365", 1.90),
            ("Betway", 1.95)
        ]
    """

    valid = [
        item
        for item in prices
        if item[1] and item[1] > 1
    ]

    if not valid:
        return None

    return max(
        valid,
        key=lambda x: x[1]
    )


def get_market_average_probability(prices):
    """
    Средняя имплайд-вероятность доступных букмекеров.
    """

    probabilities = []

    for _, odds in prices:

        probability = implied_probability(
            odds
        )

        if probability:
            probabilities.append(
                probability
            )

    if not probabilities:
        return None

    return sum(probabilities) / len(
        probabilities
    )


def calculate_value(probability, odds):

    odds = to_float(odds)

    if probability is None:
        return None

    if not odds or odds <= 1:
        return None

    return (
        probability * odds - 1
    ) * 100


def extract_markets(odds_data):

    markets = {
        "home": [],
        "draw": [],
        "away": [],
        "over_2_5": [],
        "under_2_5": [],
        "btts_yes": [],
        "btts_no": []
    }

    for bookmaker_name in (
        "Bet365",
        "Betway"
    ):

        bookmaker = odds_data.get(
            bookmaker_name
        )

        if not bookmaker:
            continue

        if isinstance(
            bookmaker,
            dict
        ):
            bookmaker_markets = list(
                bookmaker.values()
            )
        elif isinstance(
            bookmaker,
            list
        ):
            bookmaker_markets = bookmaker
        else:
            continue

        for market in bookmaker_markets:

            if not isinstance(
                market,
                dict
            ):
                continue

            name = (
                market.get("name")
                or market.get("market")
                or market.get("key")
                or ""
            )

            odds = market.get(
                "odds",
                []
            )

            if isinstance(
                odds,
                dict
            ):
                odds = [odds]

            if not isinstance(
                odds,
                list
            ):
                continue

            # =====================
            # 1X2
            # =====================

            if name.lower() == "ml":

                for odd in odds:

                    if not isinstance(
                        odd,
                        dict
                    ):
                        continue

                    home = to_float(
                        odd.get("home")
                    )

                    draw = to_float(
                        odd.get("draw")
                    )

                    away = to_float(
                        odd.get("away")
                    )

                    if home:
                        markets[
                            "home"
                        ].append(
                            (
                                bookmaker_name,
                                home
                            )
                        )

                    if draw:
                        markets[
                            "draw"
                        ].append(
                            (
                                bookmaker_name,
                                draw
                            )
                        )

                    if away:
                        markets[
                            "away"
                        ].append(
                            (
                                bookmaker_name,
                                away
                            )
                        )

            # =====================
            # TOTALS
            # =====================

            elif name.lower() == "totals":

                for odd in odds:

                    if not isinstance(
                        odd,
                        dict
                    ):
                        continue

                    line = to_float(
                        odd.get("hdp")
                    )

                    if line != 2.5:
                        continue

                    over = to_float(
                        odd.get("over")
                    )

                    under = to_float(
                        odd.get("under")
                    )

                    if over:
                        markets[
                            "over_2_5"
                        ].append(
                            (
                                bookmaker_name,
                                over
                            )
                        )

                    if under:
                        markets[
                            "under_2_5"
                        ].append(
                            (
                                bookmaker_name,
                                under
                            )
                        )

            # =====================
            # BTTS
            # =====================

            elif (
                name.lower()
                == "both teams to score"
            ):

                for odd in odds:

                    if not isinstance(
                        odd,
                        dict
                    ):
                        continue

                    yes = to_float(
                        odd.get("yes")
                        or odd.get("Yes")
                    )

                    no = to_float(
                        odd.get("no")
                        or odd.get("No")
                    )

                    if yes:
                        markets[
                            "btts_yes"
                        ].append(
                            (
                                bookmaker_name,
                                yes
                            )
                        )

                    if no:
                        markets[
                            "btts_no"
                        ].append(
                            (
                                bookmaker_name,
                                no
                            )
                        )

    return markets


def analyze_market(
    market_name,
    prices
):

    if not prices:
        return None

    best = get_best_price(
        prices
    )

    if not best:
        return None

    bookmaker, best_odds = best

    probability = (
        get_market_average_probability(
            prices
        )
    )

    value = calculate_value(
        probability,
        best_odds
    )

    return {
        "bet": market_name,
        "bookmaker": bookmaker,
        "odds": best_odds,
        "probability": (
            probability * 100
            if probability is not None
            else None
        ),
        "value": value
    }


def analyze_match(match):

    odds_data = match.get(
        "odds_data",
        {}
    )

    markets = extract_markets(
        odds_data
    )

    candidates = []

    market_names = {
        "home": "Победа хозяев",
        "draw": "Ничья",
        "away": "Победа гостей",
        "over_2_5": "ТБ 2.5",
        "under_2_5": "ТМ 2.5",
        "btts_yes": "Обе забьют — Да",
        "btts_no": "Обе забьют — Нет"
    }

    for market_key, market_name in (
        market_names.items()
    ):

        result = analyze_market(
            market_name,
            markets[market_key]
        )

        if result:
            candidates.append(
                result
            )

    if not candidates:

        return {
            "signal": False,
            "bet": None,
            "odds": None,
            "bookmaker": None,
            "probability": None,
            "value": None,
            "reason": "Недостаточно коэффициентов"
        }

    # Самый высокий Value
    best = max(
        candidates,
        key=lambda x: (
            x["value"]
            if x["value"] is not None
            else -999
        )
    )

    # Строгий первый фильтр
    if (
        best["value"] is None
        or best["value"] < 5
    ):

        return {
            "signal": False,
            "bet": best["bet"],
            "odds": best["odds"],
            "bookmaker": best["bookmaker"],
            "probability": best["probability"],
            "value": best["value"],
            "reason": "Value ниже 5%"
        }

    return {
        "signal": True,
        "bet": best["bet"],
        "odds": best["odds"],
        "bookmaker": best["bookmaker"],
        "probability": best["probability"],
        "value": best["value"],
        "reason": "Положительное Value"
            }
