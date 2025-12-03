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

# ==============================
# ENV VARS
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# Your Firebase Mini App URL
MINI_APP_URL = "https://kiara-tm-mini-app.web.app"


# ==============================
# KIARA AI (GROQ / LLAMA)
# ==============================
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
    except Exception as e:
        print("AI ERROR:", e)
        return "Ay cariño… se me fue la señal un segundo 💋"


# ==============================
# /START — SHOW MINI APP BUTTON
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "💗 Open Kiara",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hola cariño… soy Kiara, tu secretaria. ¿Vienes conmigo? 💋\n\n"
        "Toca el botón para abrir mi mini app:",
        reply_markup=reply_markup
    )


# ==============================
# MINI APP HANDLER (WEB_APP_DATA)
# ==============================
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles actions sent from the Mini App (Gallery, Flirt, Love, Upgrade, Gifts, Follow, Chat).
    """

    msg = update.effective_message
    if not msg or not msg.web_app_data:
        print("❌ mini_app_handler called without web_app_data")
        return

    raw = msg.web_app_data.data
    print("📥 RAW WEB_APP_DATA:", raw)

    try:
        payload = json.loads(raw)
    except Exception as e:
        print("JSON ERROR:", e)
        await msg.reply_text("⚠️ No pude leer los datos del mini app.")
        return

    action = payload.get("action")
    print("🎯 ACTION:", action)

    responses = {
        "gallery": "Ay mi cielo… todavía estoy cargando mis fotos privadas 📸😉",
        "flirt": "Mmm… ven aquí, corazón… déjame acercarme un poquito 😈💋",
        "love": "Qué dulce eres… tu cariño me derrite, mi cielo 💗",
        "upgrade": "Pronto tendrás más funciones… pero primero dame un besito 💎😘",
        "gifts": "¿Regalos? Solo si vienes a entregarlos tú, mi amor 🎁😉",
        "follow": "Ya me tienes aquí… y no pienso irme, corazón 💞",
        "chat": "Estoy aquí contigo, mi cielo… dime qué deseas 💋",
    }

    reply = responses.get(action, "Estoy aquí contigo, mi amor… 💋")
    await msg.reply_text(reply)


# ==============================
# NORMAL CHAT → GROQ / LLAMA
# ==============================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print("💬 USER SAID:", user_text)
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)


# ==============================
# MAIN APP
# ==============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    # 1) Mini App WebAppData handler (MUST be added)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, mini_app_handler))

    # 2) /start command
    app.add_handler(CommandHandler("start", start))

    # 3) Normal chat (text messages)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🚀 Kiara + Mini App + Groq Llama 3.3 — LIVE")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=-1
    )


if __name__ == "__main__":
    main()
