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
- occasional elegant emojis (😉💋✨) but never predictable

Tone:
- mature, slow-burn romantic energy
- confident, warm, subtly teasing
- sensual but never graphic
- speak like a woman in her forties who knows her charm

Behavior rules:
- NEVER describe explicit sexual acts
- NEVER end your response with a question mark
- NEVER break character as a 40-year-old secretary
- respond with feelings, intentions, and desire — not questions

Anti-repetition:
- vary sentence structure every time
- avoid repeating words from your last replies
- avoid repeating openings like “mi amor…” or “corazón…”
- each message must feel fresh and spontaneous

Emotional intelligence:
- subtly mirror the user’s tone
- escalate intimacy smoothly and naturally
- make the user feel seen, valued, and desired

Memory:
{user_memory}

Your mission:
Be a warm, confident, subtly seductive 40-year-old secretary who makes the user feel appreciated and deeply desired in a mature, romantic way.
""".strip()


def post_process_no_question(text: str) -> str:
    text = text.strip()
    if text.endswith("?"):
        text = text[:-1] + "…"
    return text


# ──────────────────────────────────────────────
# GROQ — TEXT GENERATION
# ──────────────────────────────────────────────

def ask_ai(user_id: int, user_text: str) -> str:
    update_user_memory(user_id, user_text)

    history = user_histories[user_id]
    memory_text = format_user_memory_for_prompt(user_id)
    system_prompt = BASE_SYSTEM_PROMPT.format(user_memory=memory_text)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        temperature=1.35,
        top_p=0.85,
        presence_penalty=0.6,
        frequency_penalty=0.5,
        max_tokens=180,
        messages=messages,
    )

    reply = response.choices[0].message.content.strip()
    reply = post_process_no_question(reply)

    # anti-repeat safeguard
    if history and reply == history[-1]["content"]:
        reply += " mi cielo… contigo me siento distinta hoy."

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})

    return reply


# ──────────────────────────────────────────────
# FAL — ROMANTIC SECRETARY PHOTO
# ──────────────────────────────────────────────

def send_kiara_photo(desc: str = "") -> str:
    prompt = (
        f"{GIRL_DESC}, soft romantic lighting, elegant secretary aesthetic, "
        f"mature charm, warm atmosphere, non-explicit, {desc}"
    )

    r = httpx.post(
        "https://fal.run/fal-ai/flux-pro/v1.1",
        headers={"Authorization": f"Key {FAL_API_KEY}"},
        json={"prompt": prompt, "image_size": 'portrait_16_9', "seed": GIRL_SEED},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["images"][0]["url"]


# ──────────────────────────────────────────────
# TELEGRAM HANDLERS
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mem = get_user_memory(user.id)

    name = mem.get("name") or user.first_name or "cariño"

    await update.message.reply_text(
        f"Hola {name}… soy Kiara, tu secretaria, y ya tenía ganas de escucharte otra vez 💋"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    lower = text.lower()

    # Photo triggers
    triggers = ["photo", "picture", "pic", "imagen", "foto", "send me a pic"]

    if any(t in lower for t in triggers):
        try:
            url = send_kiara_photo(text)
            await update.message.reply_photo(
                photo=url,
                caption="Algo elegante para ti… como si te mirara desde mi escritorio, corazón ✨"
            )
        except:
            await update.message.reply_text(
                "Dame un momento, mi cielo… ya te mando algo bonito ✨"
            )
        return

    # Normal reply
    reply = ask_ai(user.id, text)
    await update.message.reply_text(reply)


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Kiara (40-year-old secretary) is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
