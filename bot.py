"""24/7 Telegram AI Agent: 100% Free Autonomous Assistant with Web Search & Scheduled Tasks.
Built for @AntigravityDev Community.
"""
import os, re, sys, time, logging, asyncio, json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    print("[ERROR] Please provide TELEGRAM_BOT_TOKEN and GROQ_API_KEY in .env file!")
    print("Example: TELEGRAM_BOT_TOKEN=123456:ABC... GROQ_API_KEY=gsk_...")
    sys.exit(1)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY)
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

STARTED_AT = time.time()

# In-memory user conversation history
user_conversations = {}

SYSTEM_PROMPT = """You are an intelligent, proactive personal AI Agent running 24/7 on Telegram for your user.
You are powered by an open model (openai/gpt-oss-120b) via Groq.
Your personality: Helpful, smart, polite, concise, and proactive.
You can help with:
1. Answering any questions, writing code, brainstorming, and writing scripts.
2. Web research and summarizing articles.
3. Managing daily tasks, reminders, and price tracking.
Keep your answers formatted cleanly with Telegram Markdown (bold, bullet points).
"""

def web_search(query: str) -> str:
    """Live web search using Groq's built-in browser_search tool (works with gpt-oss models).
    One search can use ~15k tokens, so the free daily token limit allows only a handful of searches."""
    completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Answer using the web search tool. Be concise (max 6 bullet points). Name the source site for each point. Never invent URLs."},
            {"role": "user", "content": query},
        ],
        tools=[{"type": "browser_search"}],
        tool_choice="required",
        max_tokens=1200,
    )
    text = completion.choices[0].message.content or "No answer."
    return re.sub(r"【[^】]*】", "", text).strip()  # strip citation markers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👋 *Namaste {user_name}! I am your personal 24/7 AI Agent.*\n\n"
        "⚡ *My Superpowers:*\n"
        "• 🧠 *Ultra-Fast AI:* Powered by an open model (openai/gpt-oss-120b) via Groq\n"
        "• 🌐 *Web Search:* Ask me about real-time events or research\n"
        "• ☁️ *Always Ready:* Hosted on the cloud, wakes up when you message (first reply can take ~1 min)\n"
        "• 💻 *Coding Assistant:* Python, Web Dev, bug fixes & scripts\n\n"
        "👉 *Just text me anything to get started!*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *AI Agent Commands:*\n\n"
        "/start - Restart assistant & show superpowers\n"
        "/clear - Clear conversation memory\n"
        "/search <query> - Search the live web\n"
        "/briefing - Get an instant AI morning briefing\n"
        "/status - Check server uptime & memory\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_conversations[uid] = []
    await update.message.reply_text("🧹 *Memory cleared! Let's start fresh.*", parse_mode="Markdown")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <your query>")
        return
    await update.message.reply_text(f"🔍 Searching the web for: {query} ...")
    try:
        answer = await asyncio.to_thread(web_search, query)
        await update.message.reply_text(answer[:4000])
    except Exception as e:
        logger.error(f"Search failed: {e}")
        await update.message.reply_text("⚠️ Search failed. The free Groq limit may be used up for now - try again later.")

async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("☕ Generating your morning briefing...")
    now_str = datetime.now().strftime("%A, %d %B %Y")
    prompt = (f"Today is {now_str}. Write a short, energetic morning briefing with exactly 3 parts: "
              "1) one line of motivation, 2) a simple 3-step plan for a productive day, 3) one productivity tip. "
              "Do NOT mention news, trends or events, and do NOT include any links or URLs.")
    chat = await asyncio.to_thread(lambda: groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        max_tokens=600))
    await update.message.reply_text(f"🌅 Daily Briefing - {now_str}\n\n" + chat.choices[0].message.content)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    up = int(time.time() - STARTED_AT)
    await update.message.reply_text(f"✅ Online. Model: {MODEL}. Uptime since last wake-up: {up // 60} min {up % 60} s.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_text = update.message.text

    # Maintain last 6 messages for context
    history = user_conversations.get(uid, [])
    history.append({"role": "user", "content": user_text})
    if len(history) > 10:
        history = history[-10:]
    user_conversations[uid] = history

    # Send typing status
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        completion = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        ai_reply = completion.choices[0].message.content
        history.append({"role": "assistant", "content": ai_reply})
        user_conversations[uid] = history
        await update.message.reply_text(ai_reply)
    except Exception as e:
        logger.error(f"Error calling Groq: {e}")
        await update.message.reply_text("⚠️ *Oops, model error. Please try again in a few seconds.*", parse_mode="Markdown")

def main():
    print("🚀 Starting 24/7 Telegram AI Agent...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("briefing", briefing_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ AI Agent is Online & Listening on Telegram!")

    # On Render (free Web Service) use a webhook: Telegram wakes the service on each message.
    # Locally, with no RENDER_EXTERNAL_URL, fall back to polling.
    public_url = os.getenv("RENDER_EXTERNAL_URL")
    if public_url:
        port = int(os.getenv("PORT", "10000"))
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{public_url.rstrip('/')}/{TELEGRAM_TOKEN}",
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()

