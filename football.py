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
MAX_ODDS = 5.00

# Минимальная разница коэффициентов
MIN_BOOKMAKER_DIFF = 0.05


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
# ИМПЛАЙД-ВЕРОЯТНОСТЬ
# =================================================

def implied_probability(odds):

    odds = to_float(odds)

    if not odds or odds <= 1:
        return None

    return 1 / odds


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
# ЛУЧШИЙ КОЭФФИЦИЕНТ КАЖДОГО БУКМЕКЕРА
# =================================================

def get_best_prices(items):

    bookmakers = {}

    for item in items:

        bookmaker = item["bookmaker"]
        odds = item["odds"]

        if bookmaker not in bookmakers:
            bookmakers[bookmaker] = item
            continue

        if odds > bookmakers[bookmaker]["odds"]:
            bookmakers[bookmaker] = item

    return bookmakers


# =================================================
# ПОИСК СИГНАЛОВ
# =================================================

def find_market_signals(odds_data):

    markets = collect_markets(
        odds_data
    )

    grouped = {}

    # Группируем одинаковые рынки
    for item in markets:

        key = (
            item["market"],
            item["selection"]
        )

        if key not in grouped:
            grouped[key] = []

        grouped[key].append(item)

    signals = []

    for key, items in grouped.items():

        # =========================================
        # ОСТАВЛЯЕМ ЛУЧШУЮ ЦЕНУ ОТ КАЖДОГО
        # РЕАЛЬНОГО БУКМЕКЕРА
        # =========================================

        bookmakers = get_best_prices(
            items
        )

        # Нужны минимум 2 РАЗНЫХ букмекера
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
        second_odds = second["odds"]

        # Фильтр коэффициента
        if not (
            MIN_ODDS
            <= best_odds
            <= MAX_ODDS
        ):
            continue

        difference = (
            best_odds
            - second_odds
        )

        if difference < MIN_BOOKMAKER_DIFF:
            continue

        probability = implied_probability(
            best_odds
        )

        if probability is None:
            continue

        signals.append({

            "market":
                best["market"],

            "selection":
                best["selection"],

            "best_bookmaker":
                best["bookmaker"],

            "best_odds":
                best_odds,

            "second_bookmaker":
                second["bookmaker"],

            "second_odds":
                second_odds,

            "difference":
                difference,

            "implied_probability":
                probability,

            "bookmaker_count":
                len(bookmakers)
        })

    # Сначала самая большая разница
    signals.sort(
        key=lambda x:
            x["difference"],
        reverse=True
    )

    return signals


# =================================================
# ФОРМАТ СИГНАЛА
# =================================================

def format_signal(match, signal):

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

    market = signal["market"]

    best_bookmaker = (
        signal["best_bookmaker"]
    )

    best_odds = (
        signal["best_odds"]
    )

    second_bookmaker = (
        signal["second_bookmaker"]
    )

    second_odds = (
        signal["second_odds"]
    )

    difference = (
        signal["difference"]
    )

    probability = (
        signal["implied_probability"]
        * 100
    )

    bookmaker_count = (
        signal["bookmaker_count"]
    )

    return (
        "🔥 <b>EDGEHUNTER AI — "
        "MARKET SIGNAL</b>\n\n"

        f"🏆 <b>{league}</b>\n"

        f"⚽ <b>{home}</b> — "
        f"<b>{away}</b>\n"

        f"📅 <b>{date}</b>\n\n"

        f"🎯 <b>Рынок:</b> "
        f"{market}\n\n"

        f"💰 <b>Лучшая цена:</b> "
        f"{best_odds:.3f}\n"

        f"🏦 {best_bookmaker}: "
        f"<b>{best_odds:.3f}</b>\n"

        f"🏦 {second_bookmaker}: "
        f"{second_odds:.3f}\n\n"

        f"📈 Разница: "
        f"<b>+{difference:.3f}</b>\n"

        f"🏦 Букмекеров: "
        f"<b>{bookmaker_count}</b>\n"

        f"📊 Имплайд-вероятность: "
        f"<b>{probability:.1f}%</b>\n\n"

        "🧠 <b>Пока это рыночный сигнал, "
        "не готовый прогноз.</b>"
    )


# =================================================
# ПРОВЕРКА ФУТБОЛА
# =================================================

async def check_football():

    try:

        # Получаем матчи
        matches = get_odds_matches(
            limit=MATCH_LIMIT
        )

        await send_message(
            "⚽ <b>EDGEHUNTER AI</b>\n\n"
            f"📥 Получено матчей: "
            f"<b>{len(matches)}</b>\n"
            "🔎 Анализирую все матчи..."
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

            signals = find_market_signals(
                odds_data
            )

            for signal in signals:

                signal["match"] = match

                all_signals.append(
                    signal
                )

        # =========================================
        # НЕТ СИГНАЛОВ
        # =========================================

        if not all_signals:

            await send_message(
                "🔎 <b>EDGEHUNTER AI</b>\n\n"
                f"Проанализировано матчей: "
                f"<b>{len(matches)}</b>\n\n"
                "❌ Рыночных сигналов "
                "между разными букмекерами "
                "не найдено."
            )

            return

        # =========================================
        # СОРТИРОВКА
        # =========================================

        all_signals.sort(
            key=lambda x:
                x["difference"],
            reverse=True
        )

        top_signals = (
            all_signals[:TOP_SIGNALS]
        )

        # =========================================
        # ИТОГ
        # =========================================

        await send_message(
            "🔥 <b>EDGEHUNTER AI</b>\n\n"
            f"📊 Проанализировано матчей: "
            f"<b>{len(matches)}</b>\n"
            f"🎯 Найдено сигналов: "
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
