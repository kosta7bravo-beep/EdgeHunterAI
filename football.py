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

# Пока тестируем от +1%
MIN_VALUE = 0.01


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
        ).strftime("%d.%m.%Y %H:%M")

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

    # Две линии Bet365 считаем одним букмекером
    if name.lower().startswith("bet365"):
        return "Bet365"

    return name


# =================================================
# ИМПЛАЙД-ВЕРОЯТНОСТЬ
# =================================================

def implied_probability(odds):

    odds = to_float(odds)

    if not odds or odds <= 1:
        return None

    return 1.0 / odds


# =================================================
# НОРМАЛИЗАЦИЯ НАЗВАНИЯ РЫНКА
# =================================================

def normalize_market_name(value):

    if not value:
        return ""

    return str(value).strip().lower()


# =================================================
# СОБИРАЕМ КОЭФФИЦИЕНТЫ
# =================================================

def collect_markets(odds_data):

    result = []

    if not isinstance(odds_data, dict):
        return result

    bookmakers = odds_data.get("bookmakers", {})

    if not isinstance(bookmakers, dict):
        return result

    for raw_bookmaker, markets in bookmakers.items():

        bookmaker = normalize_bookmaker(
            raw_bookmaker
        )

        if not bookmaker:
            continue

        if not isinstance(markets, list):
            continue

        for market in markets:

            if not isinstance(market, dict):
                continue

            raw_market_name = market.get(
                "name",
                ""
            )

            market_name = normalize_market_name(
                raw_market_name
            )

            odds_list = market.get(
                "odds",
                []
            )

            if not isinstance(odds_list, list):
                continue

            # =================================================
            # 1X2
            # =================================================

            if market_name in (
                "ml",
                "1x2",
                "moneyline",
                "h2h",
                "match winner",
                "match_winner"
            ):

                for odd in odds_list:

                    if not isinstance(odd, dict):
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
                            "market": "П1",
                            "selection": "home",
                            "bookmaker": bookmaker,
                            "odds": home
                        })

                    if draw:
                        result.append({
                            "type": "1x2",
                            "market": "X",
                            "selection": "draw",
                            "bookmaker": bookmaker,
                            "odds": draw
                        })

                    if away:
                        result.append({
                            "type": "1x2",
                            "market": "П2",
                            "selection": "away",
                            "bookmaker": bookmaker,
                            "odds": away
                        })

            # =================================================
            # TOTALS
            # =================================================

            elif market_name in (
                "totals",
                "total",
                "over/under"
            ):

                for odd in odds_list:

                    if not isinstance(odd, dict):
                        continue

                    line = (
                        odd.get("hdp")
                        or odd.get("point")
                        or odd.get("line")
                    )

                    over = to_float(
                        odd.get("over")
                    )

                    under = to_float(
                        odd.get("under")
                    )

                    if line is None:
                        continue

                    line = str(line)

                    if over:

                        result.append({
                            "type": "total",
                            "market":
                                f"ТБ {line}",
                            "selection":
                                "over",
                            "bookmaker":
                                bookmaker,
                            "odds":
                                over,
                            "line":
                                line
                        })

                    if under:

                        result.append({
                            "type": "total",
                            "market":
                                f"ТМ {line}",
                            "selection":
                                "under",
                            "bookmaker":
                                bookmaker,
                            "odds":
                                under,
                            "line":
                                line
                        })

    return result


# =================================================
# ГРУППИРУЕМ ОДИН И ТОТ ЖЕ РЫНОК
# =================================================

def group_markets(markets):

    grouped = {}

    for item in markets:

        key = (
            item["type"],
            item["selection"],
            item.get("line")
        )

        if key not in grouped:
            grouped[key] = []

        grouped[key].append(item)

    return grouped


# =================================================
# ЛУЧШАЯ ЦЕНА ОТ КАЖДОГО БУКМЕКЕРА
# =================================================

def get_best_prices(items):

    bookmakers = {}

    for item in items:

        bookmaker = item["bookmaker"]
        odds = item["odds"]

        if bookmaker not in bookmakers:

            bookmakers[bookmaker] = item

        elif odds > bookmakers[bookmaker]["odds"]:

            bookmakers[bookmaker] = item

    return bookmakers


# =================================================
# FAIR PROBABILITY 1X2
# =================================================

def fair_probability_1x2(
    all_markets,
    selection
):

    bookmaker_data = {}

    for item in all_markets:

        if item["type"] != "1x2":
            continue

        bookmaker = item["bookmaker"]

        if bookmaker not in bookmaker_data:
            bookmaker_data[bookmaker] = {}

        bookmaker_data[bookmaker][
            item["selection"]
        ] = item["odds"]

    probabilities = []

    for bookmaker, prices in bookmaker_data.items():

        home = prices.get("home")
        draw = prices.get("draw")
        away = prices.get("away")

        # Без полного 1X2 рынка букмекера
        # не используем его для fair probability
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
            probability = p_home / total

        elif selection == "draw":
            probability = p_draw / total

        elif selection == "away":
            probability = p_away / total

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

    bookmaker_data = {}

    for item in items:

        bookmaker = item["bookmaker"]

        if bookmaker not in bookmaker_data:
            bookmaker_data[bookmaker] = {}

        bookmaker_data[bookmaker][
            item["selection"]
        ] = item["odds"]

    probabilities = []

    for bookmaker, prices in bookmaker_data.items():

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
            probability = p_over / total

        elif selection == "under":
            probability = p_under / total

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
# VALUE
# =================================================

def calculate_value(
    fair_probability,
    odds
):

    if fair_probability is None:
        return None

    if not odds or odds <= 1:
        return None

    return (
        fair_probability * odds
    ) - 1.0


# =================================================
# АНАЛИЗ ОДНОГО МАТЧА
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

    for key, items in grouped.items():

        market_type = key[0]
        selection = key[1]

        bookmakers = get_best_prices(
            items
        )

        # Минимум две реальные конторы
        if len(bookmakers) < 2:
            continue

        prices = list(
            bookmakers.values()
        )

        prices.sort(
            key=lambda x: x["odds"],
            reverse=True
        )

        best = prices[0]

        best_odds = best["odds"]

        if not (
            MIN_ODDS
            <= best_odds
            <= MAX_ODDS
        ):
            continue

        # =================================================
        # FAIR PROBABILITY
        # =================================================

        if market_type == "1x2":

            fair_probability = (
                fair_probability_1x2(
                    markets,
                    selection
                )
            )

        elif market_type == "total":

            fair_probability = (
                fair_probability_total(
                    items,
                    selection
                )
            )

        else:
            continue

        if fair_probability is None:
            continue

        # =================================================
        # VALUE
        # =================================================

        value = calculate_value(
            fair_probability,
            best_odds
        )

        if value is None:
            continue

        # Пока показываем только положительный Value
        if value < MIN_VALUE:
            continue

        second_odds = prices[1]["odds"]

        difference = (
            best_odds
            - second_odds
        )

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
                prices[1]["bookmaker"],

            "second_odds":
                second_odds,

            "difference":
                difference,

            "fair_probability":
                fair_probability,

            "value":
                value,

            "bookmaker_count":
                len(bookmakers),

            "market_type":
                market_type
        })

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

    fair_probability = (
        signal["fair_probability"]
        * 100
    )

    value = (
        signal["value"]
        * 100
    )

    return (
        "🔥 <b>EDGEHUNTER AI — "
        "VALUE SIGNAL</b>\n\n"

        f"🏆 <b>{league}</b>\n"

        f"⚽ <b>{home}</b> — "
        f"<b>{away}</b>\n"

        f"📅 <b>{date}</b>\n\n"

        f"🎯 <b>Рынок:</b> "
        f"{signal['market']}\n\n"

        f"🏦 <b>{signal['best_bookmaker']}</b>: "
        f"<b>{signal['best_odds']:.3f}</b>\n"

        f"🏦 {signal['second_bookmaker']}: "
        f"{signal['second_odds']:.3f}\n\n"

        f"📈 Разница цены: "
        f"+{signal['difference']:.3f}\n"

        f"🏦 Букмекеров: "
        f"<b>{signal['bookmaker_count']}</b>\n\n"

        f"📊 Fair probability: "
        f"<b>{fair_probability:.1f}%</b>\n"

        f"🔥 <b>Value: +{value:.1f}%</b>\n\n"

        "🧠 <b>ТЕСТОВЫЙ СИГНАЛ</b>\n"
        "Пока не является рекомендацией "
        "для реальной ставки."
    )


# =================================================
# ДИАГНОСТИКА
# =================================================

def diagnostic_markets(odds_data):

    markets = collect_markets(
        odds_data
    )

    if not markets:
        return (
            "❌ Не удалось разобрать "
            "ни одного рынка."
        )

    bookmakers = sorted(
        set(
            item["bookmaker"]
            for item in markets
        )
    )

    market_types = sorted(
        set(
            item["type"]
            for item in markets
        )
    )

    market_names = sorted(
        set(
            item["market"]
            for item in markets
        )
    )

    return (
        f"🏦 Букмекеры: "
        f"{', '.join(bookmakers)}\n\n"

        f"📊 Типы рынков: "
        f"{', '.join(market_types)}\n\n"

        f"🎯 Рынки: "
        f"{', '.join(market_names[:30])}\n\n"

        f"📦 Коэффициентов разобрано: "
        f"{len(markets)}"
    )


# =================================================
# ОСНОВНАЯ ПРОВЕРКА
# =================================================

async def check_football():

    try:

        matches = get_odds_matches(
            limit=MATCH_LIMIT
        )

        await send_message(
            "⚽ <b>EDGEHUNTER AI</b>\n\n"
            f"📥 Получено матчей: "
            f"<b>{len(matches)}</b>\n"
            "🧠 Проверяю рынки и Value..."
        )

        all_signals = []

        # =========================================
        # АНАЛИЗ
        # =========================================

        for index, match in enumerate(
            matches
        ):

            if not isinstance(
                match,
                dict
            ):
                continue

            odds_data = match.get(
                "odds"
            )

            if not odds_data:
                continue

            signals = find_value_signals(
                odds_data
            )

            for signal in signals:

                signal["match"] = match

                all_signals.append(
                    signal
                )

        # =========================================
        # VALUE НЕ НАЙДЕН
        # =========================================

        if not all_signals:

            # Показываем диагностику
            # по первому матчу
            diagnostic = ""

            if matches:

                first_match = matches[0]

                if isinstance(
                    first_match,
                    dict
                ):

                    diagnostic = (
                        diagnostic_markets(
                            first_match.get(
                                "odds"
                            )
                        )
                    )

            await send_message(
                "🔎 <b>EDGEHUNTER AI</b>\n\n"

                f"📊 Проанализировано матчей: "
                f"<b>{len(matches)}</b>\n\n"

                f"❌ Value-сигналов выше "
                f"{MIN_VALUE * 100:.0f}% "
                "не найдено.\n\n"

                "🔧 <b>ДИАГНОСТИКА</b>\n\n"

                f"{diagnostic}"
            )

            return

        # =========================================
        # TOP
        # =========================================

        all_signals.sort(
            key=lambda x:
                x["value"],
            reverse=True
        )

        top_signals = (
            all_signals[
                :TOP_SIGNALS
            ]
        )

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
