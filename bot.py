import logging
import os
from html import escape

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger("sportsbot")

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Public ESPN endpoints (no API key needed). Unofficial, so they can change.
SCORES_URL = "https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
TABLE_URL = "https://site.api.espn.com/apis/v2/sports/{path}/standings"

LEAGUES = {
    "epl": ("⚽ Premier League", "soccer/eng.1"),
    "laliga": ("⚽ La Liga", "soccer/esp.1"),
    "seriea": ("⚽ Serie A", "soccer/ita.1"),
    "bundes": ("⚽ Bundesliga", "soccer/ger.1"),
    "ucl": ("⚽ Champions League", "soccer/uefa.champions"),
    "nba": ("🏀 NBA", "basketball/nba"),
    "nfl": ("🏈 NFL", "football/nfl"),
    "nhl": ("🏒 NHL", "hockey/nhl"),
    "mlb": ("⚾ MLB", "baseball/mlb"),
}

http = httpx.AsyncClient(timeout=15)


def main_menu() -> InlineKeyboardMarkup:
    rows, row = [], []
    for key, (label, _) in LEAGUES.items():
        row.append(InlineKeyboardButton(label, callback_data=f"l:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def league_menu(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📅 Scores", callback_data=f"s:{key}"),
                InlineKeyboardButton("📊 Standings", callback_data=f"t:{key}"),
            ],
            [InlineKeyboardButton("⬅️ All sports", callback_data="home")],
        ]
    )


def back_menu(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"s:{key}"),
                InlineKeyboardButton("⬅️ Back", callback_data=f"l:{key}"),
            ]
        ]
    )


async def fetch_scores(path: str) -> str:
    r = await http.get(SCORES_URL.format(path=path))
    r.raise_for_status()
    events = r.json().get("events", [])
    if not events:
        return "No games scheduled right now."
    lines = []
    for ev in events[:20]:
        comp = ev["competitions"][0]
        teams = {c["homeAway"]: c for c in comp["competitors"]}
        home, away = teams.get("home"), teams.get("away")
        if not home or not away:
            continue
        status = ev["status"]["type"]
        state = status.get("state")
        if state == "pre":
            score = "vs"
        else:
            score = f"{home.get('score', '0')} - {away.get('score', '0')}"
        icon = "🔴" if state == "in" else ("✅" if state == "post" else "🕒")
        lines.append(
            f"{icon} <b>{escape(home['team']['displayName'])}</b> {score} "
            f"<b>{escape(away['team']['displayName'])}</b>\n"
            f"    <i>{escape(status.get('detail', ''))}</i>"
        )
    return "\n\n".join(lines) or "No games scheduled right now."


async def fetch_table(path: str) -> str:
    r = await http.get(TABLE_URL.format(path=path))
    r.raise_for_status()
    children = r.json().get("children", [])
    if not children:
        return "Standings are not available for this competition."
    out = []
    for group in children[:2]:
        entries = group.get("standings", {}).get("entries", [])
        if not entries:
            continue
        out.append(f"<b>{escape(group.get('name', 'Standings'))}</b>")
        for i, e in enumerate(entries[:20], 1):
            stats = {s["name"]: s.get("displayValue", "") for s in e.get("stats", [])}
            if "points" in stats:
                extra = f"{stats['points']} pts"
            else:
                extra = f"{stats.get('wins', '?')}-{stats.get('losses', '?')}"
            out.append(f"{i}. {escape(e['team']['displayName'])} — {extra}")
        out.append("")
    return "\n".join(out).strip() or "Standings are not available."


WELCOME = (
    "👋 <b>Welcome to your pocket sports companion!</b>\n\n"
    "Live scores, fixtures and standings. Pick a league below:"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        WELCOME, parse_mode=ParseMode.HTML, reply_markup=main_menu()
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n/start - open the sports menu\n/help - show this message\n\n"
        "Tap a league, then choose Scores or Standings."
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    action, _, key = q.data.partition(":")

    if action == "home":
        await q.edit_message_text(
            WELCOME, parse_mode=ParseMode.HTML, reply_markup=main_menu()
        )
        return

    if key not in LEAGUES:
        return
    label, path = LEAGUES[key]

    if action == "l":
        await q.edit_message_text(
            f"<b>{label}</b>\nWhat would you like to see?",
            parse_mode=ParseMode.HTML,
            reply_markup=league_menu(key),
        )
        return

    try:
        body = await (fetch_scores(path) if action == "s" else fetch_table(path))
    except Exception:
        log.exception("Data fetch failed")
        body = "⚠️ Couldn't load data right now. Please try again in a moment."

    title = "Scores" if action == "s" else "Standings"
    markup = back_menu(key) if action == "s" else league_menu(key)
    await q.edit_message_text(
        f"<b>{label} — {title}</b>\n\n{body}",
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
        disable_web_page_preview=True,
    )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    log.info("Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
