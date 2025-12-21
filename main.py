import asyncio
from os import getenv

from pyrogram import Client, filters
from pyrogram.errors import (
    FloodWait,
    UserAlreadyParticipant,
    UserNotParticipant,
    InviteRequestSent
)
from pyrogram.types import Message

# -------- CONFIG -------- #

API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
USERBOT_STRING = getenv("USERBOT_STRING")

userbot = Client(
    "delete_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USERBOT_STRING
)

# -------- JOIN COMMAND -------- #

@userbot.on_message(filters.command("join") & filters.me)
async def join_chat(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Usage:**\n`/join <invite link>`"
        )

    link = message.command[1]

    try:
        chat = await client.join_chat(link)

        title = chat.title or "Private Chat"

        await message.reply(
            f"✅ **Successfully Joined!**\n\n"
            f"📌 **Chat Name:** `{title}`\n"
            f"🆔 **Chat ID:** `{chat.id}`"
        )

    except InviteRequestSent:
        chat = await client.get_chat(link)
        title = chat.title or "Private Chat"

        await message.reply(
            f"⏳ **Join Request Sent!**\n\n"
            f"📌 **Chat Name:** `{title}`"
        )

    except UserAlreadyParticipant:
        chat = await client.get_chat(link)
        title = chat.title or "Private Chat"

        await message.reply(
            f"⚠️ **Already Joined**\n\n"
            f"📌 **Chat Name:** `{title}`"
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply("⏳ FloodWait complete, try again.")

    except Exception as e:
        await message.reply(f"❌ **Error:** `{e}`")

# -------- START -------- #

userbot.run()
