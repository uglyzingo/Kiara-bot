import os
from openai import OpenAI
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("BOT_TOKEN:", BOT_TOKEN)
print("OPENAI_API_KEY:", OPENAI_API_KEY)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing!")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing!")

client = OpenAI(api_key=OPENAI_API_KEY)


# ---- AI CHAT FUNCTION ----
def ask_ai(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a flirty Latina AI girlfriend. Respond lovingly and playfully."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


# ---- TELEGRAM HANDLERS ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola mi amor 😘 Tu AI girlfriend está aquí contigo 💕")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    reply = ask_ai(user_text)
    await update.message.reply_text(reply)


# ---- MAIN BOT ----
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🚀 Bot running with polling…")
    app.run_polling()


if __name__ == "__main__":
    main()
