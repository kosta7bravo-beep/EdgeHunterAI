from telegram_bot import send_message
from bbs_provider import get_matches as bbs_get_matches
from bbs_provider import get_match_stats


async def check_football():

    try:
        matches = bbs_get_matches(limit=3)

        await send_message(
            f"🧪 <b>BBS TEST</b>\n\n"
            f"Матчей получено: {len(matches)}"
        )

        if not matches:
            await send_message(
                "⚠️ BBS не вернул футбольные матчи."
            )
            return

        for match in matches[:3]:

            match_id = match.get("id")

            home = match.get("home", {})
            away = match.get("away", {})

            if isinstance(home, dict):
                home_name = home.get("name", "")
            else:
                home_name = str(home)

            if isinstance(away, dict):
                away_name = away.get("name", "")
            else:
                away_name = str(away)

            league = match.get("league", "")
            kickoff = match.get("kickoff_utc", "")

            text = (
                "⚽ <b>BBS MATCH</b>\n\n"
                f"🏆 {league}\n"
                f"⚽ {home_name} — {away_name}\n"
                f"📅 {kickoff}\n"
                f"🆔 {match_id}\n"
            )

            try:
                stats = get_match_stats(match_id)

                text += (
                    "\n📊 <b>STATS:</b>\n"
                    f"<code>{str(stats)[:1500]}</code>"
                )

            except Exception as e:

                text += (
                    "\n⚠️ STATS ERROR:\n"
                    f"<code>{str(e)[:500]}</code>"
                )

            await send_message(text)

    except Exception as e:

        await send_message(
            "❌ <b>BBS ERROR</b>\n\n"
            f"<code>{str(e)[:1000]}</code>"
            )
      
