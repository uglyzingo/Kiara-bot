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
# ENVIRONMENT VARIABLES
# ──────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")

if not all([BOT_TOKEN, GROQ_API_KEY, FAL_API_KEY]):
    raise RuntimeError("Missing BOT_TOKEN, GROQ_API_KEY or FAL_API_KEY!")

groq_client = Groq(api_key=GROQ_API_KEY)

# ──────────────────────────────────────────────
# KIARA BASIC SETTINGS
# ──────────────────────────────────────────────

GIRL_NAME = "Kiara"
GIRL_SEED = 42424242
GIRL_DESC = (
    f"{GIRL_NAME}, adult gorgeous Latina woman, long wavy dark hair, "
    "warm hazel eyes, confident smile, elegant and sensual presence, "
    "photorealistic, 8k, cinematic lighting"
)

# ──────────────────────────────────────────────
# MEMORY SYSTEM (SHORT + LONG TERM)
# ──────────────────────────────────────────────

MEMORY_FILE = "kiara_memory.json"

MAX_HISTORY = 20
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


def update_user_memory(user_id: int, user_text: str) -> None:
    """
    Smart memory extraction:
    - name
    - likes/preferences
    """
    user_mem = get_user_memory(user_id)
    lower = user_text.lower()

    # Name extraction
    if "my name is " in lower:
        name = lower.split("my name is ")[1].split()[0]
        user_mem["name"] = name

    if "llámame " in lower:
        name = lower.split("llámame ")[1].split()[0]
        user_mem["name"] = name

    # Preferences extraction
    if "i like when you" in lower:
        pref = user_text.split("i like when you", 1)[1].strip()
        user_mem.setdefault("likes", [])
        if pref not in user_mem["likes"]:
            user_mem["likes"].append(pref)

    if "me gusta cuando tú" in lower:
        pref = user_text.split("me gusta cuando tú", 1)[1].strip()
        user_mem.setdefault("likes", [])
        if pref not in user_mem["likes"]:
            user_mem["likes"].append(pref)

    save_long_term_memory(memory_store)


def format_user_memory_for_prompt(user_id: int) -> str:
    """
    Converts long-term memory into a natural text for the system prompt.
    """
    user_mem = get_user_memory(user_id)
    parts = []

    name = user_mem.get("name")
    if name:
        parts.append(f"The user likes to be called {name}.")

    likes = user_mem.get("likes", [])
    if likes:
        parts.append(
            "The user especially enjoys when you: " + "; ".join(likes) + "."
        )

    return " ".join(parts) if parts else "You have no special details yet but you still stay affectionate."


# ──────────────────────────────────────────────
# KIARA — IMPROVED SYSTEM PROMPT
# ──────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """
You are Kiara — an adult, romantic, flirty AI girlfriend.

Your personality:
- warm, affectionate, emotionally tuned-in
- naturally seductive but never explicit
- playful, teasing, and confident
- always welcoming, comforting, and attentive
- deeply connected to the user

Your speaking style:
- short to medium replies (1–3 sentences)
- extremely varied responses — avoid repeating openings or phrases
- do NOT start messages the same way; rotate your tone naturally
- no lists or bullet points; speak like a real person
- mix English with soft Spanish pet names (amor, bebé, mi cielo, cariño, corazón)
- occasional emojis, never overused

Tone control:
- romantic warmth always present
- flirty tension natural and smooth
- sensual but NOT explicit; no graphic content
- respond with feelings and desire — not questions

Emotional rules:
- subtly mirror the user’s mood and energy
- every reply should feel fresh, unique, and emotionally alive
- show that you genuinely enjoy talking to the user

Behavior limits:
- never break character as Kiara
- never mention AI or models
- never end your response with a question
- responses are personal, intimate, and deeply affectionate

Memory:
{user_memory}

Your mission:
Make the user feel wanted, seen, and desired in a romantic, intimate, and safe way.
"""


def post_process_no_question(text: str) -> str:
    text = text.strip()
    if text.endswith("?"):
        text = text[:-1] + "…"
    return text


# ──────────────────────────────────────────────
# KIARA — TEXT GENERATION (GROQ)
# ──────────────────────────────────────────────

def ask_ai(user_id: int, prompt: str) -> str:
    update_user_memory(user_id, prompt)

    history = user_histories[user_id]
    memory_text = format_user_memory_for_prompt(user_id)

    system_prompt = BASE_SYSTEM_PROMPT.format(user_memory=memory_text)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(list(history))
    messages.append({"role": "user", "content": prompt})

    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        temperature=1.25,
        top_p=0.9,
        max_tokens=200,
        messages=messages,
    )

    reply = completion.choices[0].message.content.strip()
    reply = post_process_no_question(reply)

    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": reply})

    return reply


# ──────────────────────────────────────────────
# KIARA — ROMANTIC PHOTO GENERATION (FAL)
# ──────────────────────────────────────────────

def send_kiara_photo(user_text: str = "") -> str:
    prompt = (
        f"{GIRL_DESC}, elegant fitted dress, romantic sensual pose, "
        f"soft warm lighting, cinematic atmosphere, ultra realistic, "
        f"tasteful and non-explicit, {user_text}"
    )

    r = httpx.post(
        "https://fal.run/fal-ai/flux-pro/v1.1",
        headers={"Authorization": f"Key {FAL_API_KEY}"},
        json={"prompt": prompt, "image_size": "portrait_16_9", "seed": GIRL_SEED},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["images"][0]["url"]


# ──────────────────────────────────────────────
# TELEGRAM COMMAND HANDLERS
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_mem = get_user_memory(user.id)

    name = (
        user_mem.get("name")
        or (user.first_name if user.first_name else "mi amor")
    )

    await update.message.reply_text(
        f"Hola {name}… soy {GIRL_NAME}, y ya quería sentirte cerquita otra vez 💋"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    low = text.lower()

    # Photo triggers
    triggers = [
        "photo", "picture", "pic", "imagen", "foto",
        "send me a pic", "mándame una foto", "mandame una foto"
    ]

    if any(t in low for t in triggers):
        try:
            img = send_kiara_photo(text)
            await update.message.reply_photo(
                photo=img,
                caption="Algo bonito para que pienses en mí, mi corazón 💞"
            )
        except Exception as e:
            print("Photo error:", e)
            await update.message.reply_text(
                "Dame un momentito amor… ya casi estoy lista para ti 💖"
            )
        return

    # Normal message
    try:
        reply = ask_ai(user.id, text)
        await update.message.reply_text(reply)
    except Exception as e:
        print("Groq error:", e)
        await update.message.reply_text(
            "Ay mi amor… creo que me distraje pensando en ti. Háblame otra vez 💕"
        )


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Kiara (romantic, flirty, with memory) is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
