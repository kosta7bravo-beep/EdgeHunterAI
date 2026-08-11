from telegram_bot import send_message
from odds_provider import get_odds_matches

from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# НАСТРОЙКИ
# =========================================================

MATCH_LIMIT = 20
TOP_SIGNALS = 3

MIN_ODDS = 1.50
MAX_ODDS = 8.00

# Минимальный Value для сигнала
MIN_VALUE = 0.01


# =========================================================
# ДАТА
# =========================================================

def format_date(value):

    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
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


# =========================================================
# ЛИГА
# =========================================================

def get_league_name(value):

    if isinstance(value, dict):

        return (
            value.get("name")
            or value.get("slug")
            or "—"
        )

    return str(value or "—")


# =========================================================
# ЧИСЛО
# =========================================================

def to_float(value):

    try:
        return float(value)

    except Exception:
        return None


# =========================================================
# НОРМАЛИЗАЦИЯ БУКМЕКЕРА
# =========================================================

def normalize_bookmaker(name):

    if not name:
        return ""

    name = str(name).strip()

    lower_name = name.lower()

    if lower_name.startswith("bet365"):
        return "Bet365"

    if lower_name.startswith("betway"):
        return "Betway"

    return name


# =========================================================
# СБОР РЫНКОВ
# =========================================================

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

            market_name_raw = market.get(
                "name",
                ""
            )

            market_name = str(
                market_name_raw
            ).strip()

            market_lower = market_name.lower()

            odds_list = market.get(
                "odds",
                []
            )

            if not isinstance(
                odds_list,
                list
            ):
                continue

            # =================================================
            # 1X2
            # =================================================

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

                    if home and home > 1:

                        result.append({
                            "type": "1x2",
                            "selection": "home",
                            "market": "П1",
                            "bookmaker": bookmaker,
                            "odds": home
                        })

                    if draw and draw > 1:

                        result.append({
                            "type": "1x2",
                            "selection": "draw",
                            "market": "X",
                            "bookmaker": bookmaker,
                            "odds": draw
                        })

                    if away and away > 1:

                        result.append({
                            "type": "1x2",
                            "selection": "away",
                            "market": "П2",
                            "bookmaker": bookmaker,
                            "odds": away
                        })

            # =================================================
            # TOTALS
            # =================================================

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

                    line_float = to_float(
                        line
                    )

                    if line_float is None:
                        continue

                    # Только основные футбольные тоталы
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

                    if over and over > 1:

                        result.append({
                            "type": "total",
                            "selection": "over",
                            "market": (
                                f"ТБ {line_float:g}"
                            ),
                            "bookmaker": bookmaker,
                            "odds": over,
                            "line": line_float
                        })

                    if under and under > 1:

                        result.append({
                            "type": "total",
                            "selection": "under",
                            "market": (
                                f"ТМ {line_float:g}"
                            ),
                            "bookmaker": bookmaker,
                            "odds": under,
                            "line": line_float
                        })

    return result


# =========================================================
# ГРУППИРОВКА
# =========================================================

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

        grouped[key].append(
            item
        )

    return grouped


# =========================================================
# ЛУЧШИЕ ЦЕНЫ КАЖДОГО БУКМЕКЕРА
# =========================================================

def get_best_prices(items):

    result = {}

    for item in items:

        bookmaker = item["bookmaker"]
        odds = item["odds"]

        if bookmaker not in result:

            result[bookmaker] = item

        elif odds > result[bookmaker]["odds"]:

            result[bookmaker] = item

    return result


# =========================================================
# FAIR PROBABILITY — 1X2
# =========================================================

def fair_probability_1x2(
    markets,
    selection
):

    bookmaker_prices = {}

    for item in markets:

        if item.get("type") != "1x2":
            continue

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

    for prices in bookmaker_prices.values():

        home = prices.get("home")
        draw = prices.get("draw")
        away = prices.get("away")

        if not home or not draw or not away:
            continue

        if home <= 1 or draw <= 1 or away <= 1:
            continue

        p_home = 1.0 / home
        p_draw = 1.0 / draw
        p_away = 1.0 / away

        total_probability = (
            p_home
            + p_draw
            + p_away
        )

        if total_probability <= 0:
            continue

        if selection == "home":

            fair = (
                p_home
                / total_probability
            )

        elif selection == "draw":

            fair = (
                p_draw
                / total_probability
            )

        elif selection == "away":

            fair = (
                p_away
                / total_probability
            )

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


# =========================================================
# FAIR PROBABILITY — TOTAL
# =========================================================

def fair_probability_total(
    markets,
    line,
    selection
):

    bookmaker_prices = {}

    for item in markets:

        if item.get("type") != "total":
            continue

        item_line = item.get(
            "line"
        )

        if item_line is None:
            continue

        if float(item_line) != float(line):
            continue

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

    for prices in bookmaker_prices.values():

        over = prices.get("over")
        under = prices.get("under")

        if not over or not under:
            continue

        if over <= 1 or under <= 1:
            continue

        p_over = 1.0 / over
        p_under = 1.0 / under

        total_probability = (
            p_over
            + p_under
        )

        if total_probability <= 0:
            continue

        if selection == "over":

            fair = (
                p_over
                / total_probability
            )

        elif selection == "under":

            fair = (
                p_under
                / total_probability
            )

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


# =========================================================
# УРОВЕНЬ VALUE
# =========================================================

def get_signal_level(value):

    percent = value * 100

    if percent >= 5:

        return (
            "🟢 СИЛЬНЫЙ",
            "Высокий модельный Value"
        )

    if percent >= 2:

        return (
            "🟡 СРЕДНИЙ",
            "Умеренный модельный Value"
        )

    return (
        "⚪ СЛАБЫЙ",
        "Небольшой модельный Value"
    )


# =========================================================
# ПОИСК VALUE
# =========================================================

def find_value_signals(odds_data):

    markets = collect_markets(odds_data)

    if not markets:
        return []

    grouped = group_markets(markets)

    signals = []

    debug_one_bookmaker = 0
    debug_no_fair = 0
    debug_low_value = 0
    debug_good_value = 0

    for key, items in grouped.items():

        market_type = key[0]
        selection = key[1]
        line = key[2]

        bookmakers = get_best_prices(items)

        # Нужно минимум 2 букмекера
        if len(bookmakers) < 2:
            debug_one_bookmaker += 1
            continue

        prices = sorted(
            bookmakers.values(),
            key=lambda x: x["odds"],
            reverse=True
        )

        best = prices[0]
        second = prices[1]

        best_odds = best["odds"]

        # Ограничение коэффициента
        if not (
            MIN_ODDS <= best_odds <= MAX_ODDS
        ):
            continue

        # FAIR PROBABILITY
        if market_type == "1x2":

            fair = fair_probability_1x2(
                markets,
                selection
            )

        elif market_type == "total":

            fair = fair_probability_total(
                markets,
                line,
                selection
            )

        else:
            continue

        if fair is None:
            debug_no_fair += 1
            continue

        # VALUE
        value = (
            fair * best_odds
        ) - 1.0

        if value < MIN_VALUE:
            debug_low_value += 1
            continue

        debug_good_value += 1

        level, description = get_signal_level(
            value
        )

        signals.append({

            "market": best["market"],

            "selection": selection,

            "best_bookmaker":
                best["bookmaker"],

            "best_odds":
                best_odds,

            "second_bookmaker":
                second["bookmaker"],

            "second_odds":
                second["odds"],

            "difference":
                best_odds - second["odds"],

            "fair_probability":
                fair,

            "value":
                value,

            "bookmaker_count":
                len(bookmakers),

            "level":
                level,

            "level_description":
                description
        })

    signals.sort(
        key=lambda x: x["value"],
        reverse=True
    )

    return signals


# =========================================================
# ФОРМАТ СИГНАЛА
# =========================================================

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

    fair = (
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

        f"📌 <b>Уровень:</b> "
        f"{signal['level']}\n"

        f"📝 {signal['level_description']}\n\n"

        f"💰 <b>Лучший коэффициент:</b> "
        f"<b>{signal['best_odds']:.3f}</b>\n"

        f"🏦 {signal['best_bookmaker']}: "
        f"<b>{signal['best_odds']:.3f}</b>\n"

        f"🏦 {signal['second_bookmaker']}: "
        f"{signal['second_odds']:.3f}\n\n"

        f"📈 Разница цены: "
        f"+{signal['difference']:.3f}\n"

        f"🏦 Букмекеров: "
        f"<b>{signal['bookmaker_count']}</b>\n\n"

        f"📊 Fair probability: "
        f"<b>{fair:.1f}%</b>\n"

        f"🔥 <b>Value: +{value:.1f}%</b>\n\n"

        "🧠 <b>ТЕСТОВЫЙ СИГНАЛ</b>\n"

        "Пока не является рекомендацией "
        "для реальной ставки."
    )


# =========================================================
# ДИАГНОСТИКА
# =========================================================

def diagnostic_markets(
    matches
):

    all_markets = []

    if not isinstance(
        matches,
        list
    ):
        return (
            "❌ Список матчей "
            "имеет неправильный формат."
        )

    for match in matches:

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

        parsed = collect_markets(
            odds_data
        )

        all_markets.extend(
            parsed
        )

    if not all_markets:

        return (
            "❌ Не удалось разобрать "
            "ни одного рынка."
        )

    bookmakers = sorted(
        set(
            item["bookmaker"]
            for item in all_markets
        )
    )

    market_types = sorted(
        set(
            item["type"]
            for item in all_markets
        )
    )

    market_names = sorted(
        set(
            item["market"]
            for item in all_markets
        )
    )

    return (
        f"🏦 <b>Букмекеры:</b>\n"
        f"{', '.join(bookmakers)}\n\n"

        f"📊 <b>Типы рынков:</b>\n"
        f"{', '.join(market_types)}\n\n"

        f"🎯 <b>Рынки:</b>\n"
        f"{', '.join(market_names)}\n\n"

        f"📦 <b>Позиций коэффициентов:</b> "
        f"{len(all_markets)}"
    )


# =========================================================
# ОСНОВНАЯ ПРОВЕРКА
# =========================================================

async def check_football():

    try:

        # ---------------------------------------------
        # Получаем матчи
        # ---------------------------------------------

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

        # ---------------------------------------------
        # Анализ матчей
        # ---------------------------------------------

        for match in matches:

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

        # ---------------------------------------------
        # Нет Value
        # ---------------------------------------------

        if not all_signals:

            diagnostic = diagnostic_markets(
                matches
            )

            await send_message(                "🔎 <b>EDGEHUNTER AI</b>\n\n"

                f"📊 Проанализировано матчей: "
                f"<b>{len(matches)}</b>\n\n"

                "❌ Value-сигналов выше "
                f"{MIN_VALUE * 100:.0f}% "
                "не найдено.\n\n"

                "🔧 <b>ДИАГНОСТИКА</b>\n\n"

                f"{diagnostic}"
            )

            return

        # =========================================
        # СОРТИРОВКА
        # =========================================

        all_signals.sort(
            key=lambda x: x["value"],
            reverse=True
        )

        top_signals = all_signals[
            :TOP_SIGNALS
        ]

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
        # TOP-СИГНАЛЫ
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
            
