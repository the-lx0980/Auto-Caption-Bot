import asyncio
import logging
from os import environ

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserAlreadyParticipant
from pyrogram.types import Message

# ---------------- CONFIG ---------------- #

API_ID = 37427575
API_HASH = "30c8070bf74cb5f499c6305c9bfb9717"
BOT_TOKEN = environ.get("BOT_TOKEN")


USERBOT_STRING = environ.get("USERBOT_STRING")

# IDs whose messages will NOT be deleted
WHITELIST_USERS = {
    5163706369,
    1985266909,
    2081245581
}

# ---------------- LOGGING ---------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# ---------------- CLIENTS ---------------- #

bot = Client(
    "delete_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

userbot = Client(
    name="delete_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USERBOT_STRING
)


@bot.on_message(filters.command("delall") & filters.group)
async def delete_all_handler(client: Client, msg: Message):

    chat_id = msg.chat.id

    # Admin check
    member = await client.get_chat_member(chat_id, msg.from_user.id)
    if member.status not in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ):
        return await msg.reply("❌ Admin only command")

    if not member.privileges or not member.privileges.can_delete_messages:
        return await msg.reply("❌ No delete permission")

  
    bot_id = (await client.get_me()).id
    bot_member = await client.get_chat_member(chat_id, bot_id)

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
        return await msg.reply("❌ I'm not admin")

    if not bot_member.privileges.can_delete_messages:
        return await msg.reply("❌ I need delete permission")


    try:
        await userbot.join_chat(chat_id)
    except UserAlreadyParticipant:
        pass

    status = await msg.reply("🧹 Deleting messages...")

    deleted = 0
    skipped = 0

    async for m in userbot.get_chat_history(chat_id):

        if not m.from_user:
            continue

        if m.from_user.id in WHITELIST_USERS:
            skipped += 1
            continue

        try:
            await userbot.delete_messages(chat_id, m.id)
            deleted += 1

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except Exception as e:
            log.warning(e)

    await status.edit(
        f"✅ Done\n\n"
        f"🗑 Deleted: {deleted}\n"
        f"⏭ Skipped: {skipped}"
    )

    await userbot.leave_chat(chat_id)

async def main():
    await userbot.start()
    await bot.start()
    log.info("Bot + Userbot started with STRING SESSION")
    await asyncio.Event().wait()

bot.run(main())
