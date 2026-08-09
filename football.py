from telegram_bot import send_message
from bbs_provider import get_matches, get_teams_analysis


async def check_football():

    try:
        matches = get_matches(limit=3)

        await send_message(
            f"🧪 <b>BBS TEAM TEST</b>\n\n"
            f"Матчей получено: {len(matches)}"
        )

        if not matches:
            await send_message(
                "⚠️ BBS не вернул матчи."
            )
            return

        for match in matches[:3]:

            home = match.get("home", {})
            away = match.get("away", {})

            if isinstance(home, dict):
                home_name = (
                    home.get("name")
                    or home.get("display_name")
                    or ""
                )
            else:
                home_name = str(home)

            if isinstance(away, dict):
                away_name = (
                    away.get("name")
                    or away.get("display_name")
                    or ""
                )
            else:
                away_name = str(away)

            if not home_name or not away_name:
                continue

            league = match.get("league", "")
            kickoff = (
                match.get("kickoff_utc")
                or match.get("date")
                or ""
            )

            try:

                analysis = get_teams_analysis(
                    home_name,
                    away_name
                )

                home_data = analysis["home"]
                away_data = analysis["away"]

                home_team = home_data.get("team")
                away_team = away_data.get("team")

                home_id = (
                    home_team.get("id")
                    if home_team
                    else None
                )

                away_id = (
                    away_team.get("id")
                    if away_team
                    else None
                )

                text = (
                    "⚽ <b>BBS TEAM ANALYSIS</b>\n\n"
                    f"🏆 {league}\n"
                    f"⚽ <b>{home_name}</b> — "
                    f"<b>{away_name}</b>\n"
                    f"📅 {kickoff}\n\n"
                    f"🏠 {home_name}\n"
                    f"🆔 {home_id}\n"
                    f"📈 Form: "
                    f"{str(home_data.get('form', []))[:700]}\n"
                    f"📊 Stats: "
                    f"{str(home_data.get('stats'))[:1000]}\n\n"
                    f"✈️ {away_name}\n"
                    f"🆔 {away_id}\n"
                    f"📈 Form: "
                    f"{str(away_data.get('form', []))[:700]}\n"
                    f"📊 Stats: "
                    f"{str(away_data.get('stats'))[:1000]}"
                )

                await send_message(text)

            except Exception as e:

                await send_message(
                    "⚠️ <b>BBS TEAM ERROR</b>\n\n"
                    f"⚽ {home_name} — {away_name}\n\n"
                    f"<code>{str(e)[:1000]}</code>"
                )

    except Exception as e:

        await send_message(
            "❌ <b>BBS TEST ERROR</b>\n\n"
            f"<code>{str(e)[:1000]}</code>"
                            )
      
