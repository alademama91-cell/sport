# Sports Telegram Bot

Live scores and standings for Football (EPL, La Liga, Serie A, Bundesliga, Champions League), NBA, NFL, NHL and MLB. Data comes from public ESPN endpoints, so no API key is needed.

## Run locally
```bash
pip install -r requirements.txt
export BOT_TOKEN=your_token   # Windows: set BOT_TOKEN=your_token
python bot.py
```

## Deploy (GitHub + Railway)
1. Create a bot with @BotFather and copy the token.
2. Push this folder to a GitHub repo.
3. On Railway: New Project -> Deploy from GitHub repo -> select the repo.
4. Open the service -> Variables -> add `BOT_TOKEN`.
5. Deploy. Check the logs for "Bot started".

It runs as a long-polling worker, so no domain or port is needed. Run only one instance, or Telegram will return conflict errors.

## BotFather setup
- `/setdescription` -> paste the description (max 512 chars)
- `/setabouttext` -> paste the about text (max 120 chars)
- `/setcommands`:
  ```
  start - Open the sports menu
  help - How to use the bot
  ```
