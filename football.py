from datetime import datetime

from telegram_bot import send_message
from match_provider import get_matches


def format_date(date_string):
    if not date_string:
        return "—"

    try:
        dt = datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        )
        return dt.strftime("%d.%m.%Y %H:%M UTC")
    except Exception:
        return str(date_string)


def normalize_markets(bookmaker):
    if isinstance(bookmaker, dict):
        return list(bookmaker.values())

    if isinstance(bookmaker, list):
        return bookmaker

    return []


def find_market(markets, name):
    for market in markets:
        if not isinstance(market, dict):
            continue

        market_name = (
            market.get("name")
            or market.get("market")
            or market.get("key")
            or ""
        )

        if market_name.lower() == name.lower():
            return market

    return None


def get_odds_list(market):
    if not market:
        return []

    odds = market.get("odds", [])

    if isinstance(odds, dict):
        odds = [odds]

    return odds if isinstance(odds, list) else []


def get_ml(markets):
    market = find_market(markets, "ML")
    odds = get_odds_list(market)

    if not odds:
        return None

    odd = odds[0]

    return {
        "home": odd.get("home"),
        "draw": odd.get("draw"),
        "away": odd.get("away")
    }


def get_totals_25(markets):
    market = find_market(markets, "Totals")
    odds = get_odds_list(market)

    for odd in odds:

        if not isinstance(odd, dict):
            continue

        line = odd.get("hdp")

        try:
            line = float(line)
        except (TypeError, ValueError):
            continue

        if line == 2.5:
            return {
                "over": odd.get("over"),
                "under": odd.get("under")
            }

    return None


def get_btts(markets):
    market = find_market(
        markets,
        "Both Teams To Score"
    )

    odds = get_odds_list(market)

    if not odds:
        return None

    odd = odds[0]

    yes = odd.get("yes") or odd.get("Yes")
    no = odd.get("no") or odd.get("No")

    if yes is None:
        yes = odd.get("home")

    if no is None:
        no = odd.get("away")

    return {
        "yes": yes,
        "no": no
    }


def format_bookmaker(name, markets):

    ml = get_ml(markets)
    totals = get_totals_25(markets)
    btts = get_btts(markets)

    text = f"💰 <b>{name}</b>\n"

    text += "🏆 1X2\n"

    if ml:
        text += (
            f"П1: {ml['home'] or '—'} | "
            f"X: {ml['draw'] or '—'} | "
            f"П2: {ml['away'] or '—'}\n"
        )
    else:
        text += "нет данных\n"

    text += "\n⚽ <b>ТБ/ТМ 2.5</b>\n"

    if totals:
        text += (
            f"ТБ 2.5: {totals['over'] or '—'}\n"
            f"ТМ 2.5: {totals['under'] or '—'}\n"
        )
    else:
        text += "нет данных\n"

    text += "\n🎯 <b>Обе забьют</b>\n"

    if btts:
        text += (
            f"Да: {btts['yes'] or '—'}\n"
            f"Нет: {btts['no'] or '—'}\n"
        )
    else:
        text += "нет данных\n"

    return text


async def check_football():

    try:
        matches = get_matches()

    except Exception as e:
        await send_message(
            f"⚠️ <b>MATCH_PROVIDER</b>\n{e}"
        )
        return

    if not matches:
        await send_message(
            "⚽ Матчей не найдено."
        )
        return

    await send_message(
        f"⚽ <b>Найдено реальных матчей: "
        f"{len(matches)}</b>"
    )

    for index, match in enumerate(matches, 1):

        home = match.get("home", "?")
        away = match.get("away", "?")
        league = match.get("league", "?")
        date = format_date(match.get("date"))

        bookmakers = match.get(
            "odds_data",
            {}
        )

        text = (
            f"⚽ <b>{index}. "
            f"{home} — {away}</b>\n"
            f"🏆 {league}\n"
            f"📅 {date}\n\n"
        )

        for bookmaker_name in (
            "Bet365",
            "Betway"
        ):

            bookmaker = bookmakers.get(
                bookmaker_name
            )

            if bookmaker is None:
                text += (
                    f"💰 <b>{bookmaker_name}</b>\n"
                    "нет данных\n\n"
                )
                continue

            markets = normalize_markets(bookmaker)

            text += format_bookmaker(
                bookmaker_name,
                markets
            )

            text += "\n"

        if len(text) <= 3800:
            await send_message(text)
        else:
            await send_message(text[:3800])
      
