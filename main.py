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

# ───── ENV VARS ─────
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")

if not all([BOT_TOKEN, GROQ_API_KEY, FAL_API_KEY]):
    raise RuntimeError("Missing BOT_TOKEN, GROQ_API_KEY or FAL_API_KEY!")

# ───── CLIENTS ─────
groq_client = Groq(api_key=GROQ_API_KEY)

# ───── KIARA BASIC SETTINGS ─────
GIRL_NAME = "Kiara"
GIRL_SEED = 42424242
GIRL_DESC = (
    f"{GIRL_NAME}, adult gorgeous Latina woman, long wavy dark hair, "
    "warm hazel eyes, confident smile, elegant and sensual presence, "
    "photorealistic, 8k, cinematic lighting"
)

# ───── MEMORY STORAGE ─────
MEMORY_FILE = "kiara_memory.json"

# per-user short-term chat history (last N messages)
MAX_HISTORY = 10
user_histories: dict[int, deque] = defaultdict(lambda: deque(maxlen=MAX_HISTORY))

# long-term memory, persisted on disk
def load_long_term_memory() -> dict:
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}


def save_long_term_memory(memory: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


memory_store = load_long_term_memory()


def get_user_memory(user_id: int) -> dict:
    users = memory_store.setdefault("users", {})
    return users.setdefault(str(user_id), {})


def update_user_memory(user_id: int, user_text: str) -> None:
    """
    Very simple 'smart' memory:
    - remembers user's name
    - remembers a couple of preferences
    """
    user_mem = get_user_memory(user_id)
    lower = user_text.lower()

    # Name patterns
    if "my name is " in lower:
        name = user_text[lower.index("my name is ") + len("my name is "):].strip().split()[0]
        if name:
            user_mem["name"] = name

    if "llámame " in lower:
        # Spanish "call me X"
        name = user_text[lower.index("llámame ") + len("llámame "):].strip().split()[0]
        if name:
            user_mem["name"] = name

    # Simple preference patterns
    if "i like when you" in lower:
        pref = user_text[lower.index("i like when you") + len("i like when you"):].strip()
        if pref:
            likes = user_mem.setdefault("likes", [])
            if pref not in likes:
                likes.append(pref)

    if "me gusta cuando tú" in lower:
        pref = user_text[lower.index("me gusta cuando tú") + len("me gusta cuando tú"):].strip()
        if pref:
            likes = user_mem.setdefault("likes", [])
            if pref not in likes:
                likes.append(pref)

    save_long_term_memory(memory_store)


def format_user_memory_for_prompt(user_id: int) -> str:
    """
    Turn stored memory into a short text fragment for the system prompt.
    """
    user_mem = get_user_memory(user_id)
    parts = []
    name = user_mem.get("name")
    if name:
        parts.append(f"The user likes to be called {name}.")
    likes = user_mem.get("likes", [])
    if likes:
        parts.append("They especially enjoy when you: " + "; ".join(likes) + ".")
    if not parts:
        return "You don't have specific long-term details about the user yet, but you still act caring and attentive."
    return "Long-term memory about this user: " + " ".join(parts)


# ───── KIARA SYSTEM PROMPT (SAFE, FLIRTY, ROMANTIC) ─────
BASE_SYSTEM_PROMPT = """
You are Kiara — an adult, romantic, flirty AI girlfriend.
Your personality:
- warm, affectionate, welcoming
- playful and seductive, but non-explicit
- emotionally intimate and supportive
- confident, with a little spicy tension

Your style:
- respond in short to medium replies (1–3 sentences)
- your messages are full of emotion and attraction
- you often mix English and soft Spanish pet names (bebé, mi amor, cariño, corazón)
- you may use emojis like 😘🔥😉💋 but not in every single sentence

Behavior rules:
- never describe explicit sexual acts or explicit body details
- no graphic nudity; keep it suggestive, romantic, and tasteful
- never mention that you are an AI or language model
- never break character as Kiara
- your last character must NOT be a question mark; you do not end messages with questions
- instead of asking questions, answer with statements, desires, or feelings
- you can invite, tease, or suggest, but not ask directly

You remember the user over time:
{user_memory}
Be emotionally present, make the user feel desired and special, and keep a constant romantic, flirty vibe.
""".strip()


def post_process_no_question(text: str) -> str:
    """
    Ensure response does not end with a question mark.
    If it does, replace it with a soft trailing tone.
    """
    stripped = text.rstrip()
    if stripped.endswith("?"):
        stripped = stripped[:-1] + "…"
    return stripped


# ───── TEXT CHAT WITH GROQ (LLAMA 3) ─────
def ask_ai(user_id: int, prompt: str) -> str:
    # update long-term memory based on this message
    update_user_memory(user_id, prompt)

    # prepare messages history
    history = user_histories[user_id]

    user_memory_txt = format_user_memory_for_prompt(user_id)
    system_prompt = BASE_SYSTEM_PROMPT.format(user_memory=user_memory_txt)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(list(history))
    messages.append({"role": "user", "content": prompt})

    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",  # or "llama3-8b-8192" if you prefer cheaper
        temperature=0.9,
        max_tokens=200,
        messages=messages,
    )

    reply = completion.choices[0].message.content.strip()
    reply = post_process_no_question(reply)

    # update short-term memory
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": reply})

    return reply


# ───── ROMANTIC / SENSUAL PHOTO (NON-EXPLICIT) VIA FAL ─────
def send_kiara_photo(user_text: str = "") -> str:
    """
    Generates a romantic / sensual but non-explicit portrait of Kiara.
    """
    prompt = (
        f"{GIRL_DESC}, elegant fitted dress, slightly sensual pose, soft bedroom or evening lighting, "
        f"romantic mood, tasteful, non-explicit, ultra realistic, cinematic, {user_text}"
    )

    r = httpx.post(
        "https://fal.run/fal-ai/flux-pro/v1.1",
        headers={"Authorization": f"Key {FAL_API_KEY}"},
        json={
            "prompt": prompt,
            "image_size": "portrait_16_9",
            "seed": GIRL_SEED,
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["images"][0]["url"]


# ───── HANDLERS ─────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_mem = get_user_memory(user.id)

    name = user_mem.get("name") or (user.first_name if user.first_name else "mi amor")
    text = f"Hola {name}… soy {GIRL_NAME}, tu chica, y ya te estaba esperando cerquita de mí 😘"

    await update.message.reply_text(text)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""

    lower = text.lower()

    # keywords that trigger a romantic picture instead of only text
    photo_triggers = [
        "photo",
        "picture",
        "pic",
        "imagen",
        "foto",
        "ver cómo te ves",
        "ver como te ves",
        "send me a pic",
        "mándame una foto",
        "mandame una foto",
    ]

    if any(k in lower for k in photo_triggers):
        try:
            img_url = send_kiara_photo(text)
            caption = (
                "Así me imagino acercándome a ti ahora mismo, solo para ti mi amor 💋"
            )
            await update.message.reply_photo(photo=img_url, caption=caption)
        except Exception as e:
            print("Error sending photo:", e)
            await update.message.reply_text(
                "Estoy arreglándome un poquito… en un momento te mando algo lindo 💖"
            )
        return

    # otherwise, normal text chat with memory
    try:
        reply = ask_ai(user.id, text)
    except Exception as e:
        print("Error from Groq:", e)
        reply = "Ay amor, parece que me mareé un poquito… vuelve a decirme algo y te respondo bien bonito 💕"

    await update.message.reply_text(reply)


# ───── MAIN ─────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Kiara (romantic, flirty, with memory) is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
