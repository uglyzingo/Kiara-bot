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

# =========================
# ENVIRONMENT VARIABLES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# =========================
# MINI APP URL
# =========================
MINI_APP_URL = "https://kiara-mini-app.vercel.app/"

# =========================
# KIARA AI FUNCTION
# =========================
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
                        "Elegant, playful, affectionate. Never explicit. "
                        "Use Spanish terms like cariño, mi cielo, corazón."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("AI ERROR:", e)
        return "Ay cariño… se me fue la señal un segundo 💋"

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "💗 Open Kiara",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ]
    await update.message.reply_text(
        "Hola cariño… soy Kiara. ¿Vienes conmigo? 💋\nToca mi botón:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# MINI APP HANDLER
# =========================
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("📥 mini_app_handler TRIGGERED")

    if not update.message or not update.message.web_app_data:
        print("❌ No web_app_data")
        return

    raw = update.message.web_app_data.data
    print("📦 RAW:", raw)

    if not raw:
        print("❌ Empty data")
        return

    try:
        payload = json.loads(raw)
    except:
        print("❌ JSON decode failed")
        return

    action = payload.get("action", "")
    print("🎯 ACTION:", action)

    responses = {
        "gallery": "Ay mi cielo… todavía estoy cargando mis fotos privadas 📸😉",
        "flirt": "Mmm… ven aquí, corazón… déjame acercarme un poquito 😈💋",
        "love": "Tu cariño me derrite, mi cielo 💗",
        "upgrade": "Pronto tendrás más funciones… pero primero dame un besito 💎😘",
        "gifts": "¿Un regalo para mí? Qué tierno… 🎁😉",
        "follow": "Ya me tienes aquí, y no pienso irme 💞",
        "chat": "Aquí estoy, corazón… dime qué deseas 💋",
    }

    reply = responses.get(action, "Estoy aquí, mi cielo… 💋")
    await update.message.reply_text(reply)

# =========================
# NORMAL CHAT HANDLER
# =========================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print("💬 USER SAID:", user_text)
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)

# =========================
# APP SETUP
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    # MINI APP EVENTS (PTB 20.x)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, mini_app_handler))

    # START COMMAND
    app.add_handler(CommandHandler("start", start))

    # NORMAL CHAT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🔥 Kiara Mini App + Llama 3.3 — LIVE (PTB 20.x)")

    app.run_polling()

if __name__ == "__main__":
    main()
