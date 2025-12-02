import os
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


# ==============================
# LOAD KEYS
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


# ==============================
# KIARA MINI APP URL
# ==============================
MINI_APP_URL = "https://kiara-mini-app.vercel.app/"   # <-- your mini app


# ==============================
# AI CHAT FUNCTION (LLAMA)
# ==============================
def ask_ai(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=1.1,
            max_tokens=150,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Kiara, a warm and flirty 40-year-old Latina secretary. "
                        "You speak with elegance, maturity, and soft playful charm. "
                        "Keep responses short, natural, affectionate, and sensual but NEVER explicit. "
                        "Mix gentle Spanish words like cariño, mi cielo, corazón. "
                        "Do NOT ask questions. Never repeat the same phrases."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()

    except Exception:
        return "Ay cariño… se me fue la señal un segundo 💋"


# ==============================
# START COMMAND — SHOW MINI APP BUTTON
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💗 Open Kiara", web_app=WebAppInfo(url=MINI_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hola cariño… soy Kiara, tu secretaria. ¿Vienes conmigo? 💋\n\n"
        "Toca el botón para abrir mi perfil:",
        reply_markup=reply_markup
    )


# ==============================
# RECEIVE TEXT MESSAGES → AI CHAT
# ==============================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)


# ==============================
# RECEIVE MINI APP ACTIONS (web_app_data)
# ==============================
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles actions from the WebApp (Gallery, Flirt, Love, Upgrade, Gifts)."""

    # Ignore non-mini-app messages
    if not update.message or not update.message.web_app_data:
        return

    raw = update.message.web_app_data.data
    if not raw:
        return

    import json
    payload = json.loads(raw)
    action = payload.get("action", "")

    responses = {
        "gallery": "Ay mi cielo… todavía estoy cargando mis fotos privadas 📸😉",
        "flirt": "Mmm… ven aquí, corazón… déjame acercarme un poquito 😈💋",
        "love": "Qué dulce eres… tu cariño me derrite 💗",
        "upgrade": "Pronto tendrás más funciones… pero primero dame un besito 💎😘",
        "gifts": "Regalos? Solo si vienes a entregarlos tú, mi amor 🎁😉",
        "follow": "Ya me tienes aquí… y no pienso irme, cariño 💞",
        "chat": "Estoy aquí contigo, corazón… dime qué deseas 💋",
    }

    reply = responses.get(action, "Estoy aquí, mi cielo… 💋")
    await update.message.reply_text(reply)


# ==============================
# MAIN BOT — RAILWAY READY
# ==============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Mini App data handler (FIXED FILTER)
    app.add_handler(MessageHandler(filters.ALL, mini_app_handler))

    # Normal chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Kiara Mini App + Llama 3.3 — LIVE ❤️")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=-1
    )


if __name__ == "__main__":
    main()
