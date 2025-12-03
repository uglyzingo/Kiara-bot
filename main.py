import os, asyncio, json
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# KEYS
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing keys")

client = Groq(api_key=GROQ_API_KEY)
MINI_APP_URL = "https://kiara-mini-app.vercel.app/"

# DIRTY TALK
def ask_ai(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=1.1,
            max_tokens=180,
            messages=[
                {"role": "system", "content": "You are Kiara, a warm and flirty 40-year-old Latina secretary. You speak with elegance, maturity, and soft playful charm. Keep responses short, natural, affectionate, and sensual but NEVER explicit. Mix gentle Spanish words like cariño, mi cielo, corazón. Do NOT ask questions. Never repeat the same phrases."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except:
        return "Ay cariño… se me fue la señal un segundo 💋"

# /START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💗 Open Kiara", web_app=WebAppInfo(url=MINI_APP_URL))]]
    await update.message.reply_text(
        "Hola cariño… soy Kiara, tu secretaria. ¿Vienes conmigo? 💋\n\nToca el botón para abrir mi perfil:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# NORMAL CHAT
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = ask_ai(update.message.text)
    await update.message.reply_text(reply)

# MINI APP HANDLER — MUST BE LAST
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.web_app_data:
        return
    try:
        payload = json.loads(update.message.web_app_data.data)
        action = payload.get("action", "")
        responses = {
            "gallery": "Ay mi cielo… todavía estoy cargando mis fotos privadas 📸😉",
            "flirt": "Mmm… ven aquí, corazón… déjame acercarme un poquito 😈💋",
            "love": "Qué dulce eres… tu cariño me derrite 💗",
            "upgrade": "Muy pronto tendrás funciones premium… pero primero un besito 💎😘",
            "gifts": "¿Regalos? Solo si vienes a entregarlos tú, mi amor 🎁😉",
            "follow": "Ya me tienes aquí… y no pienso irme, cariño 💞",
            "chat": "Estoy aquí contigo… dime qué deseas 💋",
        }
        await update.message.reply_text(responses.get(action, "Estoy aquí, mi cielo… 💋"))
    except:
        pass

# MAIN — UNBREAKABLE
async def run():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))           # ← normal chat first
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, mini_app_handler))  # ← Mini App LAST

    print("Kiara Mini App + Llama 3.3 — LIVE & UNBREAKABLE")
    
    await app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=-1,
        close_loop=False
    )

if __name__ == "__main__":
    asyncio.run(run())
