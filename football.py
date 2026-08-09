from telegram_bot import send_message
from bbs_provider import (
    get_matches,
    get_teams_analysis,
    check_bbs_coverage
)


def pct(value):
    if value is None:
        return "—"

    try:
        return f"{float(value) * 100:.0f}%"
    except Exception:
        return str(value)


def team_summary(data):
    stats = data.get("stats") or {}

    return (
        f"📈 Форма: {stats.get('form_string', '—')}\n"
        f"🏆 Очки: {stats.get('points', '—')}\n"
        f"⚽ Забито: {stats.get('goals_scored', '—')}\n"
        f"🥅 Пропущено: {stats.get('goals_conceded', '—')}\n"
        f"🧤 Сухие матчи: {stats.get('clean_sheets', '—')}\n"
        f"🎯 BTTS: {pct(stats.get('btts_rate'))}\n"
        f"🔥 ТБ 2.5: {pct(stats.get('over_2_5_rate'))}\n"
        f"📊 Средние забитые: "
        f"{stats.get('avg_goals_scored', '—')}"
    )


async def check_football():

    try:coverage = check_bbs_coverage()

await send_message(
    f"📡 <b>BBS COVERAGE</b>\n\n"
    f"<code>{str(coverage)[:3500]}</code>"
)
        matches = get_matches(limit=3)

        await send_message(
            f"⚽ <b>EDGEHUNTER AI — BBS</b>\n\n"
            f"Получено матчей: <b>{len(matches)}</b>"
        )

        for match in matches:

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

                home_data = analysis.get("home") or {}
                away_data = analysis.get("away") or {}

                text = (
                    "🔎 <b>EDGEHUNTER AI — АНАЛИЗ</b>\n\n"
                    f"🏆 {league}\n"
                    f"⚽ <b>{home_name}</b> — "
                    f"<b>{away_name}</b>\n"
                    f"📅 {kickoff}\n\n"

                    f"🏠 <b>{home_name}</b>\n"
                    f"{team_summary(home_data)}\n\n"

                    f"✈️ <b>{away_name}</b>\n"
                    f"{team_summary(away_data)}\n\n"

                    "🧠 <b>Пока только статистический анализ.</b>\n"
                    "Коэффициент и Value подключим следующим этапом."
                )

                await send_message(text)

            except Exception as e:

                await send_message(
                    "⚠️ <b>BBS ANALYSIS ERROR</b>\n\n"
                    f"⚽ {home_name} — {away_name}\n\n"
                    f"<code>{str(e)[:1000]}</code>"
                )

    except Exception as e:

        await send_message(
            "❌ <b>FOOTBALL ERROR</b>\n\n"
            f"<code>{str(e)[:1000]}</code>"
                )
      
