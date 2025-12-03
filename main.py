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
