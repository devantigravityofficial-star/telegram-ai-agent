# Telegram AI Agent (free)

A Telegram bot powered by `openai/gpt-oss-120b` on Groq. `/search` uses Groq's built-in web search and returns sources.

## Commands
`/start`, `/help`, `/clear`, `/search <query>`, `/briefing`, `/status`, or just chat.

## Setup
1. Create a bot with @BotFather and copy the token.
2. Create a free key at https://console.groq.com.
3. Deploy to Render as a **Web Service** (Free plan) from this repo. Start command: `python bot.py`.
   Set `TELEGRAM_BOT_TOKEN` and `GROQ_API_KEY` as environment variables.

## Honest limits (checked 5 Nov 2026; they can change)
- Render free web services sleep after 15 minutes without traffic. The first reply after sleeping takes about 30-60 seconds.
- Groq free limits for this model: 30 requests/minute, 1,000 requests/day, 200K tokens/day. One web search uses about 16K tokens.
- Locally, create a `.env` file with the two variables and run `python bot.py` (uses polling).
