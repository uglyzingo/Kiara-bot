from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import json
import os
from openai import OpenAI

# Load keys
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# ===========================
# /start COMMAND
# ===========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola amor 💕\nEstoy lista para ti.\n\nPresiona Chat o cualquier botón del Mini App.",
        parse_mode="Markdown"
    )


# ===========================
# MINI-APP HANDLER
# ===========================
async def mini_app_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.effective_message.web_app_data.data
    data = json.loads(raw)

    action = data.get("action")

    if action == "chat":
        await update.message.reply_text("💋 Ven aquí... ¿de qué quieres hablar, mi amor?")
    
    elif action == "follow":
        await update.message.reply_text("✨ Te sigo a donde vayas…")
    
    elif action == "gallery":
        await update.message.reply_text("📸 Aquí tienes mi galería… pronto más 😉")
    
    elif action == "flirt":
        await update.message.reply_text("😈 Mmm… sabes despertar cosas en mí…")
    
    elif action == "love":
        await update.message.reply_text("💗 Te mando todo mi amor, cariño…")
    
    elif action == "upgrade":
        await update.message.reply_text("💎 Muy pronto vendrán funciones premium…")


# ===========================
# APPLICATION
# ===========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Mini App WebAppData listener
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, mini_app_handler))

    # /start
    app.add_handler(CommandHandler("start", start))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
