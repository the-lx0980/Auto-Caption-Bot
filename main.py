from pyrogram import Client, filters, enums
from os import environ
from openai import OpenAI

# ───────────────────────────────
# 🔧 CONFIG
# ───────────────────────────────
API_ID = 24456380
API_HASH = "fe4d4eb35510370ea1073fbcb36e1fcc"
BOT_TOKEN = environ.get("BOT_TOKEN")

FROM_CHAT_ID = -1001572995585   # Source channel
TO_CHAT_ID = -1001592628992     # Target channel

OPENAI_API_KEY = environ.get("OPENAI_API_KEY")

# ───────────────────────────────
# 🚀 INITIALIZE
# ───────────────────────────────
app = Client("webxzonebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
ai = OpenAI(api_key=OPENAI_API_KEY)

# ───────────────────────────────
# 🧠 AI FUNCTION - CAPTION PARSER
# ───────────────────────────────
def extract_caption_ai(caption: str):
    prompt = f"""
You are a movie and series caption analyzer.

Your task:
1. Detect whether the caption refers to a **movie** or a **series**.
2. Extract and reformat details properly using the following rules.

────────────────────────────
🎬 FOR MOVIES:
Format:
<Movie Name> (<Year>) <Quality> <Print> <Audio>

Example:
Venom (2021) 1080p WEB-DL Dual Audio (Hindi + English)

────────────────────────────
📺 FOR SERIES:
Format:
<Series Name> (<Year>) S<SeasonNo:02d> E<EpisodeNo:02d> <Quality> <Print> <Audio>

Example:
Loki (2023) S01 E03 1080p WEB-DL Dual Audio (Hindi + English)

Notes:
- Always write Season and Episode as S01, E01 (not “Season 1”, “Episode 1”)
- “Season 11” → “S11”, “Episode 111” → “E111”
- Keep spacing clean and consistent.
- If data is missing, skip it gracefully (don’t guess).
- Output plain text only (no Markdown or emojis).

────────────────────────────
Input caption:
{caption}

Now return only the formatted caption.
    """

    try:
        response = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("AI Error:", e)
        return caption  # fallback if AI fails


# ───────────────────────────────
# 📦 MESSAGE HANDLER
# ───────────────────────────────
@app.on_message(filters.channel)
async def forward(bot, message):
    try:
        if not message.caption:
            return

        new_caption = await extract_caption_ai(message.caption)
        print(f"Old: {message.caption}\nNew: {new_caption}\n{'-'*40}")

        await bot.copy_message(
            chat_id=TO_CHAT_ID,
            from_chat_id=FROM_CHAT_ID,
            message_id=message.id,
            caption=new_caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )

    except Exception as e:
        print(f"Error forwarding: {e}")


# ───────────────────────────────
# 🔄 START COMMAND
# ───────────────────────────────
@app.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("✅ Bot is Alive and Ready!")


# ───────────────────────────────
# ▶️ RUN BOT
# ───────────────────────────────
print("🤖 Bot Started!")
app.run()
