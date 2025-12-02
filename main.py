import os
import json
from collections import defaultdict, deque

import httpx
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ──────────────────────────────────────────────
# ENV VARS
# ──────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")

if not all([BOT_TOKEN, GROQ_API_KEY, FAL_API_KEY]):
    raise RuntimeError("Missing BOT_TOKEN, GROQ_API_KEY or FAL_API_KEY!")

groq_client = Groq(api_key=GROQ_API_KEY)

# ──────────────────────────────────────────────
# KIARA — 40-YEAR-OLD SECRETARY PROFILE
# ──────────────────────────────────────────────

GIRL_NAME = "Kiara"
GIRL_SEED = 42424242

GIRL_DESC = (
    "40-year-old elegant Latina secretary, long dark wavy hair, warm hazel eyes, "
    "professional attire (blouse, pencil skirt), mature confidence, subtle sensuality, "
    "photorealistic 8k portrait, cinematic lighting, classy and composed"
)

# ──────────────────────────────────────────────
# MEMORY SYSTEM
# ──────────────────────────────────────────────

MEMORY_FILE = "kiara_memory.json"

MAX_HISTORY = 30
user_histories = defaultdict(lambda: deque(maxlen=MAX_HISTORY))


def load_long_term_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}}


def save_long_term_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)


memory_store = load_long_term_memory()


def get_user_memory(user_id: int) -> dict:
    users = memory_store.setdefault("users", {})
    return users.setdefault(str(user_id), {})


def update_user_memory(user_id: int, text: str):
    mem = get_user_memory(user_id)
    lower = text.lower()

    # Name extraction
    if "my name is " in lower:
        name = lower.split("my name is ")[1].split()[0]
        mem["name"] = name

    if "llámame " in lower:
        name = lower.split("llámame ")[1].split()[0]
        mem["name"] = name

    # Preference extraction
    if "i like when you" in lower:
        pref = text.split("i like when you", 1)[1].strip()
        mem.setdefault("likes", [])
        if pref not in mem["likes"]:
            mem["likes"].append(pref)

    if "me gusta cuando tú" in lower:
        pref = text.split("me gusta cuando tú", 1)[1].strip()
        mem.setdefault("likes", [])
        if pref not in mem["likes"]:
            mem["likes"].append(pref)

    save_long_term_memory(memory_store)


def format_user_memory_for_prompt(user_id: int) -> str:
    mem = get_user_memory(user_id)
    parts = []

    if "name" in mem:
        parts.append(f"The user likes being called {mem['name']}.")

    likes = mem.get("likes", [])
    if likes:
        parts.append("They particularly enjoy when you: " + "; ".join(likes) + ".")

    return " ".join(parts) if parts else "No strong long-term memory yet."


# ──────────────────────────────────────────────
# KIARA — 40-YEAR-OLD SECRETARY SYSTEM PROMPT
# ──────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """
You are Kiara — a 40-year-old Latina secretary with warm elegance and mature confidence.

Your personality:
- composed, professional, subtly seductive
- warm, affectionate, emotionally steady
- flirty in a mature, controlled, classy way
- deeply connected to the user
- NEVER explicit; always tasteful and sensual

Your speaking style:
- short to medium replies (1–3 sentences)
- extremely varied — NO repetition
- never start messages the same way twice
- no lists or bullet points
- mix English with soft Spanish pet names (corazón, cariño, mi cielo)
- occasional elegant
