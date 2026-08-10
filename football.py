from telegram_bot import send_message
from odds_provider import get_odds_matches

from datetime import datetime
from zoneinfo import ZoneInfo


# =================================================
# НАСТРОЙКИ
# =================================================

MATCH_LIMIT = 20
TOP_PREDICTIONS = 3
TOP_VALUE = 3

MIN_ODDS = 1.50
MAX_ODDS = 8.00

# Минимальный Value для отдельного Value-сигнала
MIN_VALUE = 0.01

# Минимальная вероятность для рыночного прогноза
MIN_PREDICTION_PROB = 0.50


# =================================================
# ДАТА
# =================================================

def format_date(value):

    if not value:
        return "—"

    try:

        dt = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00"
            )
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=ZoneInfo("UTC")
            )

        return dt.astimezone(
            ZoneInfo("Europe/Kyiv")
        ).strftime(
            "%d.%m.%Y %H:%M"
        )

    except Exception:

        return str(value)


# =================================================
# ЛИГА
# =================================================

def get_league_name(value):

    if isinstance(value, dict):

        return (
            value.get("name")
            or value.get("slug")
            or "—"
        )

    return str(value or "—")


# =================================================
# ЧИСЛО
# =================================================

def to_float(value):

    try:
        return float(value)

    except Exception:
        return None


# =================================================
# БУКМЕКЕР
# =================================================

def normalize_bookmaker(name):

    if not name:
        return ""

    name = str(name).strip()

    if name.lower().startswith("bet365"):
        return "Bet365"

    if name.lower().startswith("betway"):
        return "Betway"

    return name


# =================================================
# IMPLIED PROBABILITY
# =================================================

def implied_probability(odds):

    odds = to_float(odds)

    if not odds or odds <= 1:
        return None

    return 1.0 / odds


# =================================================
# СБОР РЫНКОВ
# =================================================

def collect_markets(odds_data):

    result = []

    if not isinstance(
        odds_data,
        dict
    ):
        return result

    bookmakers = odds_data.get(
        "bookmakers",
        {}
    )

    if not isinstance(
        bookmakers,
        dict
    ):
        return result

    for bookmaker_name, markets in bookmakers.items():

        bookmaker = normalize_bookmaker(
            bookmaker_name
        )

        if not bookmaker:
            continue

        if not isinstance(
            markets,
            list
        ):
            continue

        for market in markets:

            if not isinstance(
                market,
                dict
            ):
                continue

            market_name = str(
                market.get(
                    "name",
                    ""
                )
            ).strip()

            market_lower = (
                market_name.lower()
            )

            odds_list = market.get(
                "odds",
                []
            )

            if not isinstance(
                odds_list,
                list
            ):
                continue

            # =====================================
            # 1X2
            # =====================================

            if market_lower in (
                "ml",
                "1x2",
                "moneyline",
                "h2h",
                "match winner",
                "match_winner"
            ):

                for odd in odds_list:

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

                        result.append({
                            "type": "1x2",
                            "selection": "home",
                            "market": "П1",
                            "bookmaker": bookmaker,
                            "odds": home
                        })

                    if draw:

                        result.append({
                            "type": "1x2",
                            "selection": "draw",
                            "market": "X",
                            "bookmaker": bookmaker,
                            "odds": draw
                        })

                    if away:

                        result.append({
                            "type": "1x2",
                            "selection": "away",
                            "market": "П2",
                            "bookmaker": bookmaker,
                            "odds": away
                        })

            # =====================================
            # TOTALS
            # =====================================

            elif market_lower in (
                "totals",
                "total",
                "goals over/under",
                "over/under"
            ):

                for odd in odds_list:

                    if not isinstance(
                        odd,
                        dict
                    ):
                        continue

                    line = (
                        odd.get("hdp")
                        or odd.get("point")
                        or odd.get("line")
                    )

                    if line is None:
                        continue

                    try:

                        line_float = float(
                            line
                        )

                    except Exception:

                        continue

                    # Только основные футбольные линии
                    allowed_lines = (
                        1.5,
                        2.5,
                        3.0,
                        3.5
                    )

                    if line_float not in allowed_lines:
                        continue

                    over = to_float(
                        odd.get("over")
                    )

                    under = to_float(
                        odd.get("under")
                    )

                    if over:

                        result.append({
                            "type": "total",
                            "selection": "over",
                            "market":
                                f"ТБ {line_float:g}",
                            "bookmaker":
                                bookmaker,
                            "odds":
                                over,
                            "line":
                                line_float
                        })

                    if under:

                        result.append({
                            "type": "total",
                            "selection": "under",
                            "market":
                                f"ТМ {line_float:g}",
                            "bookmaker":
                                bookmaker,
                            "odds":
                                under,
                            "line":
                                line_float
                        })

    return result


# =================================================
# ГРУППИРОВКА
# =================================================

def group_markets(markets):

    grouped = {}

    for item in markets:

        key = (
            item["type"],
            item["selection"],
            item.get("line")
        )

        grouped.setdefault(
            key,
            []
        ).append(item)

    return grouped


# =================================================
# ЛУЧШАЯ ЦЕНА КАЖДОГО БУКМЕКЕРА
# =================================================

def get_best_prices(items):

    result = {}

    for item in items:

        bookmaker = item[
            "bookmaker"
        ]

        if (
            bookmaker not in result
            or item["odds"]
            > result[bookmaker]["odds"]
        ):

            result[bookmaker] = item

    return result


# =================================================
# FAIR PROBABILITY 1X2
# =================================================

def fair_probability_1x2(
    markets,
    selection
):

    bookmakers = {}

    for item in markets:

        if item["type"] != "1x2":
            continue

        bookmaker = item[
            "bookmaker"
        ]

        bookmakers.setdefault(
            bookmaker,
            {}
        )[item["selection"]] = (
            item["odds"]
        )

    probabilities = []

    for prices in bookmakers.values():

        home = prices.get(
            "home"
        )

        draw = prices.get(
            "draw"
        )

        away = prices.get(
            "away"
        )

        if not home or not draw or not away:
            continue

        p_home = 1.0 / home
        p_draw = 1.0 / draw
        p_away = 1.0 / away

        total = (
            p_home
            + p_draw
            + p_away
        )

        if total <= 0:
            continue

        if selection == "home":

            probability = (
                p_home / total
            )

        elif selection == "draw":

            probability = (
                p_draw / total
            )

        elif selection == "away":

            probability = (
                p_away / total
            )

        else:

            continue

        probabilities.append(
            probability
        )

    if not probabilities:
        return None

    return (
        sum(probabilities)
        / len(probabilities)
    )


# =================================================
# FAIR PROBABILITY TOTAL
# =================================================

def fair_probability_total(
    items,
    selection
):

    bookmakers = {}

    for item in items:

        bookmaker = item[
            "bookmaker"
        ]

        bookmakers.setdefault(
            bookmaker,
            {}
        )[item["selection"]] = (
            item["odds"]
        )

    probabilities = []

    for prices in bookmakers.values():

        over = prices.get(
            "over"
        )

        under = prices.get(
            "under"
        )

        if not over or not under:
            continue

        p_over = 1.0 / over
        p_under = 1.0 / under

        total = (
            p_over
            + p_under
        )

        if total <= 0:
            continue

        if selection == "over":

            probability = (
                p_over / total
            )

        elif selection == "under":

            probability = (
                p_under / total
            )

        else:

            continue

        probabilities.append(
            probability
        )

    if not probabilities:
        return None

    return (
        sum(probabilities)
        / len(probabilities)
    )


# =================================================
# УРОВЕНЬ ПРОГНОЗА
# =================================================

def prediction_level(
    probability
):

    percent = probability * 100

    if percent >= 65:

        return (
            "🟢 ВЫСОКИЙ",
            "Сильное рыночное преимущество"
        )

    if percent >= 58:

        return (
            "🟡 ХОРОШИЙ",
            "Хорошая рыночная вероятность"
        )

    if percent >= 50:

        return (
            "🟠 УМЕРЕННЫЙ",
            "Умеренная рыночная вероятность"
        )

    return (
        "⚪ СЛАБЫЙ",
        "Низкая рыночная вероятность"
    )


# =================================================
# ПОИСК ПРОГНОЗОВ
# =================================================

def find_predictions(
    odds_data
):

    markets = collect_markets(
        odds_data
    )

    if not markets:
        return []

    grouped = group_markets(
        markets
    )

    predictions = []

    # =============================================
    # 1X2
    # =============================================

    for selection in (
        "home",
        "draw",
        "away"
    ):

        fair = fair_probability_1x2(
            markets,
            selection
        )

        if fair is None:
            continue

        # Находим лучшую цену этого исхода
        items = [
            item
            for item in markets
            if (
                item["type"] == "1x2"
                and item["selection"]
                == selection
            )
        ]

        bookmakers = get_best_prices(
            items
        )

        if len(bookmakers) < 2:
            continue

        prices = sorted(
            bookmakers.values(),
            key=lambda x: x["odds"],
            reverse=True
        )

        best = prices[0]

        if not (
            MIN_ODDS
            <= best["odds"]
            <= MAX_ODDS
        ):
            continue

        if fair < MIN_PREDICTION_PROB:
            continue

        value = (
            fair * best["odds"]
        ) - 1.0

        level, description = (
            prediction_level(
                fair
            )
        )

        predictions.append({

            "type": "1x2",

            "market":
                best["market"],

            "selection":
                selection,

            "best_odds":
                best["odds"],

            "best_bookmaker":
                best["bookmaker"],

            "fair_probability":
                fair,

            "value":
                value,

            "bookmaker_count":
                len(bookmakers),

            "level":
                level,

            "description":
                description
        })

    # =============================================
    # TOTALS
    # =============================================

    for key, items in grouped.items():

        market_type = key[0]

        if market_type != "total":
            continue

        selection = key[1]

        fair = fair_probability_total(
            items,
            selection
        )

        if fair is None:
            continue

        bookmakers = get_best_prices(
            items
        )

        if len(bookmakers) < 2:
            continue

        prices = sorted(
            bookmakers.values(),
            key=lambda x: x["odds"],
            reverse=True
        )

        best = prices[0]

        if not (
            MIN_ODDS
            <= best["odds"]
            <= MAX_ODDS
        ):
            continue

        if fair < MIN_PREDICTION_PROB:
            continue

        value = (
            fair * best["odds"]
        ) - 1.0

        level, description = (
            prediction_level(
                fair
            )
        )

        predictions.append({

            "type": "total",

            "market":
                best["market"],

            "selection":
                selection,

            "best_odds":
                best["odds"],

            "best_bookmaker":
                best["bookmaker"],

            "fair_probability":
                fair,

            "value":
                value,

            "bookmaker_count":
                len(bookmakers),

            "level":
                level,

            "description":
                description
        })

    # Сначала вероятность,
    # затем Value
    predictions.sort(
        key=lambda x: (
            x["fair_probability"],
            x["value"]
        ),
        reverse=True
    )

    return predictions


# =================================================
# ПОИСК VALUE
# =================================================

def find_value_signals(
    odds_data
):

    markets = collect_markets(
        odds_data
    )

    if not markets:
        return []

    grouped = group_markets(
        markets
    )

    signals = []

    for key, items in grouped.items():

        market_type = key[0]
        selection = key[1]

        bookmakers = get_best_prices(
            items
        )

        if len(bookmakers) < 2:
            continue

        prices = sorted(
            bookmakers.values(),
            key=lambda x: x["odds"],
            reverse=True
        )

        best = prices[0]
        second = prices[1]

        best_odds = best["odds"]

        if not (
            MIN_ODDS
            <= best_odds
            <= MAX_ODDS
        ):
            continue

        if market_type == "1x2":

            fair = fair_probability_1x2(
                markets,
                selection
            )

        elif market_type == "total":

            fair = fair_probability_total(
                items,
                selection
            )

        else:

            continue

        if fair is None:
            continue

        value = (
            fair * best_odds
        ) - 1.0

        if value < MIN_VALUE:
            continue

        signals.append({

            "market":
                best["market"],

            "selection":
                selection,

            "best_bookmaker":
                best["bookmaker"],

            "best_odds":
                best_odds,

            "second_bookmaker":
                second["bookmaker"],

            "second_odds":
                second["odds"],

            "difference":
                best_odds
                - second["odds"],

            "fair_probability":
                fair,

            "value":
                value,

            "bookmaker_count":
                len(bookmakers)
        })

    signals.sort(
        key=lambda x: x["value"],
        reverse=True
    )

    return signals


# =================================================
# ФОРМАТ ПРОГНОЗА
# =================================================

def format_prediction(
    match,
    prediction
):

    home = (
        match.get("home")
        or "—"
    )

    away = (
        match.get("away")
        or "—"
    )

    league = get_league_name(
        match.get("league")
    )

    date = format_date(
        match.get("date")
    )

    probability = (
        prediction[
            "fair_probability"
        ] * 100
    )

    value = (
        prediction["value"]
        * 100
    )

    return (
        "🔮 <b>EDGEHUNTER AI — "
        "РЫНОЧНЫЙ ПРОГНОЗ</b>\n\n"

        f"🏆 <b>{league}</b>\n"

        f"⚽ <b>{home}</b> — "
        f"<b>{away}</b>\n"

        f"📅 <b>{date}</b>\n\n"

        f"🎯 <b>Прогноз:</b> "
        f"<b>{prediction['market']}</b>\n\n"

        f"📌 <b>Уровень:</b> "
        f"{prediction['level']}\n"

        f"📝 {prediction['description']}\n\n"

        f"📊 Рыночная вероятность: "
        f"<b>{probability:.1f}%</b>\n"

        f"💰 Лучший коэффициент: "
        f"<b>{prediction['best_odds']:.3f}</b>\n"

        f"🏦 {prediction['best_bookmaker']}\n"

        f"🏦 Букмекеров: "
        f"<b>{prediction['bookmaker_count']}</b>\n\n"

        f"🔥 Value: "
        f"<b>{value:+.1f}%</b>\n\n"

        "🧠 <b>Тестовый рыночный прогноз.</b>\n"
        "Это не гарантия результата и пока "
        "не является рекомендацией для реальной ставки."
    )


# =================================================
# ФОРМАТ VALUE
# =================================================

def format_value_signal(
    match,
    signal
):

    home = (
        match.get("home")
       
