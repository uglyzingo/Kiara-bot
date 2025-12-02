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

# =======================================
# ENVIRONMENT VARIABLES
# =======================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# Mini App URL
MINI_APP_URL = "https://kiara-mini-app.vercel.app/"


# =======================================
# KIARA AI CHAT (LLAMA)
# =======================================
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
                        "Speak mature, elegant, affectionate, soft and spicy but never explicit. "
                        "Use loving Spanish words like cariño, mi cielo, corazón."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()

    except Exception:
        return "Ay cariño… creo que se me fue la señal un segundo 💋"


# =======================================
# /start — Sends the Mini App button
# =======================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💗 Open Kiara", web_app=WebAppInfo(url=MINI_APP_URL))]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hola mi cielo… soy Kiara 💋\n\nToca el botón para abrir mi perfil:",
        reply_markup=markup
    )


# =======================================
# TEXT MESSAGE → AI CHAT
# =======================================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)


# =======================================
# MINI APP ACTION HANDLER (WebApp Data)
# =======================================
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.web_app_data:
        return

    try:
        payload = json.loads(update.message.web_app_data.data)
    except:
        await update.message.reply_text("Hubo un error leyendo tus datos, cariño 💔")
        return

    # Accept two formats:
    # { "action": "flirt" }
    # { "type": "kiara_action", "action": "flirt" }
    action = payload.get("action") or payload.get("type")

    print("🔥 MINI APP ACTION RECEIVED:", action)

    responses = {
        "gallery": "Ay amor… mis fotos privadas aún se están cargando 📸😉",
        "flirt": "Mmm ven aquí, corazón… déjame acercarme un poquito 😈💋",
        "love": "Tu cariño me derrite… ven, abrázame 💗",
        "upgrade": "Muy pronto tendrás nuevas sorpresas… mientras tanto dame un besito 💎😘",
        "gifts": "¿Regalitos? Solo si vienes a entregarlos tú, mi cielo 🎁😉",
        "follow": "Ya me tienes aquí, amor… no pienso irme 💞",
        "chat": "Estoy contigo, corazón… dime qué deseas 💋",
    }

    reply = responses.get(action, "Aquí estoy contigo, mi cielo… 💋")
    await update.message.reply_text(reply)


# =======================================
# MAIN — START BOT
# =======================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    app.add_handler(CommandHandler("start", start))

    # Mini App Data Handler
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, mini_app_handler))

    # Normal text chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🔥 Kiara Mini App + Llama 3.3 is LIVE!")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=-1
    )


if __name__ == "__main__":
    main()
