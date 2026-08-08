        
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
            "⚽ Матчей сейчас не найдено."
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

            markets = bookmakers.get(
                bookmaker_name
            )

            if markets is None:
                text += (
                    f"💰 <b>{bookmaker_name}</b>\n"
                    "❌ данных нет\n\n"
                )
                continue

            if isinstance(markets, dict):
                markets = list(markets.values())

            if not isinstance(markets, list):
                text += (
                    f"💰 <b>{bookmaker_name}</b>\n"
                    "❌ неизвестный формат данных\n\n"
                )
                continue

            text += format_bookmaker(
                bookmaker_name,
                markets
            )

            text += "\n"

        # Пока просто показываем реальные данные.
        # Прогнозы подключим после проверки.
        if len(text) > 3800:
            await send_message(text[:3800])
        else:
            await se
