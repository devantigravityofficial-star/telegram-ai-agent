"""24/7 Telegram AI Agent: 100% Free Autonomous Assistant with Web Search & Scheduled Tasks.
Built for @AntigravityDev Community.
"""
import os, sys, logging, asyncio, json, requests
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

# In-memory user conversation history
user_conversations = {}

SYSTEM_PROMPT = """You are an intelligent, proactive personal AI Agent running 24/7 on Telegram for your user.
You are powered by Llama 3.3 70B via Groq.
Your personality: Helpful, smart, polite, concise, and proactive.
You can help with:
1. Answering any questions, writing code, brainstorming, and writing scripts.
2. Web research and summarizing articles.
3. Managing daily tasks, reminders, and price tracking.
Keep your answers formatted cleanly with Telegram Markdown (bold, bullet points).
"""

def duckduckgo_search(query: str, max_results: int = 3) -> str:
    """Free web search using DuckDuckGo Instant Answer API."""
    try:
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1&skip_disambig=1"
        resp = requests.get(url, timeout=10).json()
        abstract = resp.get("AbstractText", "")
        if abstract:
            return f"Web Search Result for '{query}':\n{abstract}"
        # Related topics fallback
        topics = [t.get("Text", "") for t in resp.get("RelatedTopics", [])[:max_results] if "Text" in t]
        if topics:
            return f"Web Search Results for '{query}':\n" + "\n".join(f"- {t}" for t in topics)
        return "No direct web answer found, will answer from knowledge base."
    except Exception as e:
        return f"Web search temporarily unavailable: {e}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👋 *Namaste {user_name}! I am your personal 24/7 AI Agent.*\n\n"
        "⚡ *My Superpowers:*\n"
        "• 🧠 *Ultra-Fast AI:* Powered by Llama 3.3 70B via Groq\n"
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
        await update.message.reply_text("Usage: `/search <your query>`", parse_mode="Markdown")
        return
    await update.message.reply_text(f"🔍 *Searching the web for:* `{query}`...", parse_mode="Markdown")
    res = duckduckgo_search(query)
    # Summarize with AI
    prompt = f"Summarize these search results clearly for the user:\n\n{res}"
    chat = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a concise researcher."}, {"role": "user", "content": prompt}]
    )
    await update.message.reply_text(chat.choices[0].message.content)

async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("☕ *Generating your AI Morning Briefing...*", parse_mode="Markdown")
    now_str = datetime.now().strftime("%A, %d %B %Y")
    prompt = f"Today is {now_str}. Generate an energetic, productive 4-point morning briefing covering top tech trends, motivation, and a daily productivity tip."
    chat = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    await update.message.reply_text(f"🌅 *Daily Briefing — {now_str}*\n\n" + chat.choices[0].message.content, parse_mode="Markdown")

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
            model="llama-3.3-70b-versatile",
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

