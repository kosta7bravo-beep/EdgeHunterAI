from telegram_bot import send_message
from odds_provider import get_odds_matches

from datetime import datetime
from zoneinfo import ZoneInfo


# =================================================
# НАСТРОЙКИ
# =================================================

MATCH_LIMIT = 20
TOP_SIGNALS = 3

MIN_ODDS = 1.50
MAX_ODDS = 8.00

# Минимальный Value для сигнала
MIN_VALUE = 0.03


# =================================================
# ДАТА
# =================================================

def format_date(value):

    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
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
# НОРМАЛИЗАЦИЯ БУКМЕКЕРА
# =================================================

def normalize_bookmaker(name):

    if not name:
        return ""

    name = str(name).strip()

    # Bet365 и Bet365 (no latency)
    # считаем ОДНИМ букмекером
    if name.lower().startswith("bet365"):
        return "Bet365"

    if name.lower().startswith("betway"):
        return "Betway"

    return name


# =================================================
# ИМПЛАЙД
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

    if not isinstance(odds_data, dict):
        return result

    bookmakers = odds_data.get(
        "bookmakers",
        {}
    )

    if not isinstance(bookmakers, dict):
        return result

    for bookmaker_name, markets in bookmakers.items():

        bookmaker = normalize_bookmaker(
            bookmaker_name
        )

        if not bookmaker:
            continue

        if not isinstance(markets, list):
            continue

        for market in markets:

            if not isinstance(market, dict):
                continue

            market_name = str(
                market.get("name", "")
            ).lower()

            odds_list = market.get(
                "odds",
                []
            )

            if not isinstance(
                odds_list,
                list
            ):
                continue

            for odd in odds_list:

                if not isinstance(odd, dict):
                    continue

                # =================================
                # 1X2
                # =================================

                if market_name in (
                    "ml",
                    "1x2",
                    "moneyline"
                ):

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
                            "market": "П1",
                            "selection": "home",
                            "bookmaker": bookmaker,
                            "odds": home
                        })

                    if draw:
                        result.append({
                            "market": "X",
                            "selection": "draw",
                            "bookmaker": bookmaker,
                            "odds": draw
                        })

                    if away:
                        result.append({
                            "market": "П2",
                            "selection": "away",
                            "bookmaker": bookmaker,
                            "odds": away
                        })

                # =================================
                # TOTALS
                # =================================

                elif market_name in (
                    "totals",
                    "total"
                ):

                    line = odd.get("hdp")

                    over = to_float(
                        odd.get("over")
                    )

                    under = to_float(
                        odd.get("under")
                    )

                    if line is not None:

                        if over:
                            result.append({
                                "market":
                                    f"ТБ {line}",
                                "selection":
                                    "over",
                                "bookmaker":
                                    bookmaker,
                                "odds":
                                    over
                            })

                        if under:
                            result.append({
                                "market":
                                    f"ТМ {line}",
                                "selection":
                                    "under",
                                "bookmaker":
                                    bookmaker,
                                "odds":
                                    under
                            })

    return result


# =================================================
# ЛУЧШИЕ ЦЕНЫ КАЖДОГО БУКМЕКЕРА
# =================================================

def get_best_prices(items):

    bookmakers = {}

    for item in items:

        bookmaker = item["bookmaker"]
        odds = item["odds"]

        if bookmaker not in bookmakers:

            bookmakers[bookmaker] = item

        elif odds > bookmakers[
            bookmaker
        ]["odds"]:

            bookmakers[bookmaker] = item

    return bookmakers


# =================================================
# ГРУППИРОВКА РЫНКОВ
# =================================================

def group_markets(markets):

    grouped = {}

    for item in markets:

        key = (
            item["market"],
            item["selection"]
        )

        if key not in grouped:
            grouped[key] = []

        grouped[key].append(
            item
        )

    return grouped


# =================================================
# FAIR PROBABILITY ДЛЯ 1X2
# =================================================

def calculate_fair_probability_1x2(
    all_markets,
    selection
):

    # Группируем по букмекеру
    bookmaker_markets = {}

    for item in all_markets:

        bookmaker = item["bookmaker"]

        if bookmaker not in bookmaker_markets:
            bookmaker_markets[
                bookmaker
            ] = {}

        bookmaker_markets[
            bookmaker
        ][
            item["selection"]
        ] = item["odds"]

    probabilities = []

    for bookmaker, prices in (
        bookmaker_markets.items()
    ):

        home = prices.get("home")
        draw = prices.get("draw")
        away = prices.get("away")

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
            fair = p_home / total

        elif selection == "draw":
            fair = p_draw / total

        elif selection == "away":
            fair = p_away / total

        else:
            continue

        probabilities.append(
            fair
        )

    if not probabilities:
        return None

    return (
        sum(probabilities)
        / len(probabilities)
    )


# =================================================
# FAIR PROBABILITY ДЛЯ TOTALS
# =================================================

def calculate_fair_probability_2way(
    all_markets,
    selection
):

    bookmaker_prices = {}

    for item in all_markets:

        bookmaker = item["bookmaker"]

        if bookmaker not in bookmaker_prices:
            bookmaker_prices[
                bookmaker
            ] = {}

        bookmaker_prices[
            bookmaker
        ][
            item["selection"]
        ] = item["odds"]

    probabilities = []

    for bookmaker, prices in (
        bookmaker_prices.items()
    ):

        over = prices.get("over")
        under = prices.get("under")

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
            fair = p_over / total

        elif selection == "under":
            fair = p_under / total

        else:
            continue

        probabilities.append(
            fair
        )

    if not probabilities:
        return None

    return (
        sum(probabilities)
        / len(probabilities)
    )


# =================================================
# ПОИСК VALUE
# =================================================

def find_value_signals(odds_data):

    markets = collect_markets(
        odds_data
    )

    if not markets:
        return []

    grouped = group_markets(
        markets
    )

    signals = []

    # =============================================
    # ОБРАБАТЫВАЕМ КАЖДЫЙ РЫНОК
    # =============================================

    for key, items in grouped.items():

        market_name = key[0]
        selection = key[1]

        # Лучшие цены каждого букмекера
        bookmakers = get_best_prices(
            items
        )

        # Нужны минимум 2 РАЗНЫХ букмекера
        if len(bookmakers) < 2:
            continue

        prices = list(
            bookmakers.values()
        )

        # Лучшая цена
        best = max(
            prices,
            key=lambda x: x["odds"]
        )

        best_odds = best["odds"]

        if not (
            MIN_ODDS
            <= best_odds
            <= MAX_ODDS
        ):
            continue

        # =========================================
        # FAIR PROBABILITY
        # =========================================

        # 1X2
        if selection in (
            "home",
            "draw",
            "away"
        ):

            # Собираем все 1X2 рынки
            # всех букмекеров для этого матча.
            fair_probability = (
                calculate_fair_probability_1x2(
                    markets,
                    selection
                )
            )

        # Totals
        elif selection in (
            "over",
            "under"
        ):

            # Здесь нужно учитывать
            # конкретную линию тотала.
            same_line_items = []

            for item in markets:

                if (
                    item["market"]
                    == market_name
                ):
                    same_line_items.append(
                        item
                    )

            fair_probability = (
                calculate_fair_probability_2way(
                    same_line_items,
                    selection
                )
            )

        else:
            continue

        if fair_probability is None:
            continue

        # =========================================
        # VALUE
        # =========================================

        value = (
            fair_probability
            * best_odds
        ) - 1.0

        # Не показываем отрицательный Value
        if value < MIN_VALUE:
            continue

        # =========================================
        # РАЗНИЦА БУКМЕКЕРОВ
        # =========================================

        second_best = sorted(
            prices,
            key=lambda x: x["odds"],
            reverse=True
        )

        second_odds = (
            second_best[1]["odds"]
        )

        difference = (
            best_odds
            - second_odds
        )

        signals.append({

            "market":
                market_name,

            "selection":
                selection,

            "best_bookmaker":
                best["bookmaker"],

            "best_odds":
                best_odds,

            "second_bookmaker":
                second_best[1][
                    "bookmaker"
                ],

            "second_odds":
                second_odds,

            "difference":
                difference,

            "fair_probability":
                fair_probability,

            "value":
                value,

            "bookmaker_count":
                len(bookmakers)
        })

    # =============================================
    # СОРТИРОВКА ПО VALUE
    # =============================================

    signals.sort(
        key=lambda x:
            x["value"],
        reverse=True
    )

    return signals


# =================================================
# ФОРМАТ СИГНАЛА
# =================================================

def format_signal(
    match,
    signal
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

    market = signal[
        "market"
    ]

    best_bookmaker = signal[
        "best_bookmaker"
    ]

    best_odds = signal[
        "best_odds"
    ]

    second_bookmaker = signal[
        "second_bookmaker"
    ]

    second_odds = signal[
        "second_odds"
    ]

    difference = signal[
        "difference"
    ]

    fair_probability = (
        signal[
            "fair_probability"
        ]
        * 100
    )

    value = (
        signal["value"]
        * 100
    )

    bookmaker_count = (
        signal["bookmaker_count"]
    )

    return (
        "🔥 <b>EDGEHUNTER AI — "
        "VALUE SIGNAL</b>\n\n"

        f"🏆 <b>{league}</b>\n"

        f"⚽ <b>{home}</b> — "
        f"<b>{away}</b>\n"

        f"📅 <b>{date}</b>\n\n"

        f"🎯 <b>Рынок:</b> "
        f"{market}\n\n"

        f"💰 <b>Лучший коэффициент:</b> "
        f"<b>{best_odds:.3f}</b>\n"

        f"🏦 {best_bookmaker}: "
        f"<b>{best_odds:.3f}</b>\n"

        f"🏦 {second_bookmaker}: "
        f"{second_odds:.3f}\n\n"

        f"📈 Разница цены: "
        f"+{difference:.3f}\n"

        f"🏦 Букмекеров: "
        f"<b>{bookmaker_count}</b>\n\n"

        f"📊 Fair probability: "
        f"<b>{fair_probability:.1f}%</b>\n"

        f"🔥 <b>Value: +{value:.1f}%</b>\n\n"

        "🧠 <b>Это модельный рыночный "
        "сигнал. Пока тестируем.</b>"
    )


# =================================================
# ОСНОВНАЯ ПРОВЕРКА
# =================================================

async def check_football():

    try:

        # =========================================
        # ПОЛУЧАЕМ МАТЧИ
        # =========================================

        matches = get_odds_matches(
            limit=MATCH_LIMIT
        )

        await send_message(
            "⚽ <b>EDGEHUNTER AI</b>\n\n"
            f"📥 Получено матчей: "
            f"<b>{len(matches)}</b>\n"
            "🧠 Рассчитываю рыночную "
            "вероятность и Value..."
        )

        all_signals = []

        # =========================================
        # АНАЛИЗ ВСЕХ МАТЧЕЙ
        # =========================================

        for match in matches:

            if not isinstance(
                match,
                dict
            ):
                continue

            odds_data = match.get(
                "odds"
            )

            signals = find_value_signals(
                odds_data
            )

            for signal in signals:

                signal["match"] = match

                all_signals.append(
                    signal
                )

        # =========================================
        # НЕТ VALUE
        # =========================================

        if not all_signals:

            await send_message(
                "🔎 <b>EDGEHUNTER AI</b>\n\n"
                f"📊 Проанализировано матчей: "
                f"<b>{len(matches)}</b>\n\n"
                "❌ Value-сигналов выше "
                f"{MIN_VALUE * 100:.0f}% "
                "не найдено.\n\n"
                "Это нормально: модель "
                "не будет заставлять нас "
                "делать ставку."
            )

            return

        # =========================================
        # TOP VALUE
        # =========================================

        all_signals.sort(
            key=lambda x:
                x["value"],
            reverse=True
        )

        top_signals = (
            all_signals[:TOP_SIGNALS]
        )

        # =========================================
        # ИТОГ
        # =========================================

        await send_message(
            "🔥 <b>EDGEHUNTER AI — "
            "VALUE SCAN</b>\n\n"

            f"📊 Матчей: "
            f"<b>{len(matches)}</b>\n"

            f"🎯 Value-сигналов: "
            f"<b>{len(all_signals)}</b>\n"

            f"🏆 TOP: "
            f"<b>{len(top_signals)}</b>"
        )

        # =========================================
        # TOP-3
        # =========================================

        for signal in top_signals:

            await send_message(
                format_signal(
                    signal["match"],
                    signal
                )
            )

    except Exception as e:

        await send_message(
            "❌ <b>FOOTBALL ERROR</b>\n\n"
            f"<code>{str(e)[:2000]}</code>"
  )
