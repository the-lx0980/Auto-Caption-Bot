import asyncio
from os import getenv

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import (
    FloodWait,
    UserAlreadyParticipant,
    InviteRequestSent,
    InviteHashExpired,
    ChannelInvalid,
    ChannelPrivate,
    ChatRestricted,
    PeerIdInvalid
)
from pyrogram.types import Message

# ---------------- CONFIG ---------------- #

API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
USERBOT_STRING = getenv("USERBOT_STRING")

userbot = Client(
    "delete_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USERBOT_STRING
)

# ---------------- /JOIN ---------------- #

@userbot.on_message(filters.command("join"))
async def join_chat(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage:\n`/join <invite_link>`")

    link = message.command[1]

    try:
        chat = await client.join_chat(link)
        title = chat.title or "Private Chat"

        await message.reply(
            f"✅ **Joined Successfully**\n\n"
            f"📌 **Chat:** `{title}`\n"
            f"🆔 **ID:** `{chat.id}`"
        )

    except InviteRequestSent:
        chat = await client.get_chat(link)
        await message.reply(
            f"⏳ **Join Request Sent**\n\n"
            f"📌 **Chat:** `{chat.title}`"
        )

    except UserAlreadyParticipant:
        chat = await client.get_chat(link)
        await message.reply(
            f"⚠️ **Already Joined**\n\n"
            f"📌 **Chat:** `{chat.title}`"
        )

    except InviteHashExpired:
        await message.reply(
            "❌ **Invite Link Expired / Invalid**\n"
            "👉 New invite link try karo"
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)

    except Exception as e:
        await message.reply(f"❌ **Error:** `{e}`")

# ---------------- /LEAVE <chat_id> ---------------- #

@userbot.on_message(filters.command("leave"))
async def leave_chat(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage:\n`/leave <chat_id>`")

    try:
        chat_id = int(message.command[1])
        await client.leave_chat(chat_id)

        await message.reply(
            f"✅ **Left Chat Successfully**\n"
            f"🆔 **Chat ID:** `{chat_id}`"
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)

    except Exception as e:
        await message.reply(f"❌ **Error:** `{e}`")

# ---------------- /LEAVE_BANNED ---------------- #

@userbot.on_message(filters.command("leave_banned"))
async def leave_banned_chats(client: Client, message: Message):
    left = 0
    scanned = 0

    status = await message.reply("🔍 **Scanning Telegram-banned chats...**")

    async for dialog in client.get_dialogs():
        chat = dialog.chat

        if chat.type not in (
            ChatType.CHANNEL,
            ChatType.SUPERGROUP,
            ChatType.GROUP
        ):
            continue

        scanned += 1

        try:
            # Try to access chat
            await client.get_chat(chat.id)

        except (
            ChannelInvalid,
            ChannelPrivate,
            ChatRestricted,
            PeerIdInvalid
        ):
            try:
                await client.leave_chat(chat.id)
                left += 1
                await asyncio.sleep(1)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                continue

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except Exception:
            continue

    await status.edit(
        f"✅ **Cleanup Completed**\n\n"
        f"🔍 **Scanned:** `{scanned}`\n"
        f"🚪 **Banned Chats Left:** `{left}`"
    )

# ---------------- START ---------------- #

userbot.run()
