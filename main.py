import os
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Load keys
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing!")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing!")

groq_client = Groq(api_key=GROQ_API_KEY)


# ---- AI CHAT FUNCTION (LLAMA) ----
def ask_ai(prompt: str) -> str:
    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        temperature=1.1,
        messages=[
            {
                "role": "system",
                "content":
                "You are Kiara, a warm and flirty 40-year-old Latina secretary. "
                "You speak with elegance, maturity, and soft playful charm. "
                "Keep responses short, natural, affectionate, and sensual but NEVER explicit. "
                "Mix gentle Spanish words like cariño, mi cielo, corazón. "
                "Do NOT ask questions. Never repeat the same phrases."
            },
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content.strip()


# ---- TELEGRAM HANDLERS ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola cariño… soy Kiara, tu secretaria. Ven aquí, que ya quería escucharte 💋"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)


# ---- MAIN BOT ----
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🚀 Kiara (Llama) running with polling…")
    app.run_polling()


if __name__ == "__main__":
    main()
