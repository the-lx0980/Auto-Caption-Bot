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
async def extract_caption_ai(caption: str):
    prompt = f"""
You are a movie caption analyzer.
Extract the following details accurately and create a neat caption:
- Movie name
- Release year
- Quality (e.g. 720p, 1080p, 4K)
- Audio languages (Hindi, English, Dual, etc.)
- Size (if mentioned)

Input caption:
{caption}

Return your answer in **pure text**, formatted nicely for Telegram.
Example format:
🎬 Movie Name (2024)
📽️ 1080p WEB-DL | Dual Audio (Hindi + English)
📦 Size: 2.3GB
#Action #Movie
"""

    try:
        response = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("AI Error:", e)
        return caption  # fallback to original caption if AI fails


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
