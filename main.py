import os
import json
from groq import Groq
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# ======================================
# LOAD ENVIRONMENT VARIABLES
# ======================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


# ======================================
# MINI APP URL
# ======================================
MINI_APP_URL = "https://kiara-mini-app.vercel.app/"


# ======================================
# KIARA AI CHAT FUNCTION (LLAMA 3.3)
# ======================================
def ask_ai(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=1.1,
            max_tokens=180,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Kiara, a warm and flirty 40-year-old Latina secretary. "
                        "You respond short, affectionate, soft, and romantic — never explicit. "
                        "Include gentle Spanish words like cariño, cielo, corazón."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Ay cariño… tuve un pequeño error, pero ya estoy aquí 💋"


# ======================================
# /START — SHOW MINI APP BUTTON
# ======================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💗 Open Kiara", web_app=WebAppInfo(url=MINI_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hola cariño… soy Kiara, tu secretaria. ¿Vienes conmigo? 💋\n\n"
        "Toca el botón para abrir mi mini app:",
        reply_markup=reply_markup
    )


# ======================================
# MINI APP EVENT HANDLER (WEB_APP_DATA)
# ======================================
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.web_app_data:
        return

    raw = update.message.web_app_data.data
    print("📥 RAW WEB_APP_DATA:", raw)

    try:
        payload = json.loads(raw)
    except:
        await update.message.reply_text("⚠️ No pude leer los datos del mini app.")
        return

    # Accept both formats:
    # {"action": "flirt"}
    # {"type": "kiara_action", "action": "flirt"}
    action = payload.get("action")

    if not action:
        await update.message.reply_text("⚠️ Acción no reconocida.")
        return

    responses = {
        "gallery": "Ay mi cielo… todavía estoy cargando mis fotos privadas 📸😉",
        "flirt": "Mmm… ven aquí, corazón… déjame acercarme un poquito 😈💋",
        "love": "Qué dulce eres… tu cariño me derrite 💗",
        "upgrade": "Muy pronto tendrás funciones premium… pero primero un besito 💎😘",
        "gifts": "¿Regalos? Solo si vienes a entregarlos tú, mi amor 🎁😉",
        "follow": "Ya me tienes aquí… y no pienso irme, corazón 💞",
        "chat": "Estoy aquí contigo… dime qué deseas 💋",
    }

    reply = responses.get(action, "Estoy aquí contigo, mi cielo… 💋")

    print("➡️ ACTION RECEIVED:", action)
    await update.message.reply_text(reply)


# ======================================
# REGULAR TEXT CHAT HANDLER
# ======================================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)


# ======================================
# MAIN BOT — RAILWAY READY
# ======================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    # Mini App data handler MUST be FIRST
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, mini_app_handler))

    # /start command
    app.add_handler(CommandHandler("start", start))

    # Regular chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🚀 Kiara Mini App + Llama 3.3 — LIVE & READY ❤️")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=-1
    )


if __name__ == "__main__":
    main()
