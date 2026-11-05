# Telegram AI Agent (free)

A Telegram bot powered by Llama 3.3 70B on Groq, with DuckDuckGo web search.

## Setup
1. Create a bot with @BotFather and copy the token.
2. Create a free key at https://console.groq.com.
3. Deploy to Render as a **Web Service** (free plan) using `render.yaml`.
   Set `TELEGRAM_BOT_TOKEN` and `GROQ_API_KEY` as environment variables.

## Notes
- Render's free web services spin down after 15 minutes without traffic. The first reply after idle can take about a minute.
- Check Groq's rate-limit page for current free-tier limits.
- Locally, create a `.env` file with the two variables and run `python bot.py` (uses polling).
