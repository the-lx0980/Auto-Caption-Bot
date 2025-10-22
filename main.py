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
