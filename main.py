import asyncio
import logging
from os import getenv

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserAlreadyParticipant
from pyrogram.types import Message, ChatPrivileges, InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIG ---------------- #

API_ID = int(getenv("API_ID", 0))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN")
USERBOT_STRING = getenv("USERBOT_STRING")
OWNERS = set(int(x) for x in getenv("OWNERS", "").split(",") if x.strip())
MSG_IDS = set(int(x) for x in getenv("MSG_IDS", "0").split(",") if x.strip())
WHITELIST_USERS = set(
    int(x) for x in getenv("WHITELIST_USERS", "0").split(",") if x.strip()
)

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
    "delete_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USERBOT_STRING
)

# ---------------- START COMMAND ---------------- #

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, msg: Message):

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/thelx0980")
            ],
            [
                InlineKeyboardButton("📦 Source Code", url="https://github.com/lx0980/group-delete-all")
            ]
        ]
    )

    if msg.from_user.id in OWNERS:
        text = (
            "👋 **Hello Owner!**\n\n"
            "🧹 Use `/delgrpall` in groups where:\n"
            "• Bot is admin\n"
            "• Userbot can be invited\n\n"
            "⚠️ Use carefully (FloodWait may occur)"
        )
    else:
        text = "❌ This bot is personal/private use only.\n\n💡 Make your own using this repo.\nhttps://github.com/lx0980/group-delete-all"

    await msg.reply(
        text,
        reply_markup=buttons
    )

# ---------------- DELETE ALL COMMAND ---------------- #

@bot.on_message(filters.command("delgrpall") & filters.group)
async def delete_all_handler(client: Client, msg: Message):

    # Only owners can use
    if msg.from_user.id not in OWNERS:
        return await msg.reply("❌ You are not a bot owner")

    chat_id = msg.chat.id

    # ---- Admin check (command sender) ----
    member = await client.get_chat_member(chat_id, msg.from_user.id)
    if member.status not in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ):
        return await msg.reply("❌ Admin only command")

    if not member.privileges or not member.privileges.can_delete_messages:
        return await msg.reply("❌ No delete permission")

    # ---- Bot admin check ----
    bot_id = (await client.get_me()).id
    bot_member = await client.get_chat_member(chat_id, bot_id)

    if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
        return await msg.reply("❌ I'm not admin")

    if not bot_member.privileges.can_delete_messages:
        return await msg.reply("❌ I need delete permission")

    if not bot_member.privileges.can_invite_users:
        return await msg.reply("❌ I need invite permission")

    if not bot_member.privileges.can_promote_members:
        return await msg.reply("❌ I need promote permission")

    status = await msg.reply("🧹 Preparing deletion...")

    userbot_id = (await userbot.get_me()).id
    need_leave = False

    # ---- Ensure userbot is member ----
    try:
        await client.get_chat_member(chat_id, userbot_id)

    except Exception:
        invite = await client.create_chat_invite_link(chat_id)

        try:
            await userbot.join_chat(invite.invite_link)
            need_leave = True
        except UserAlreadyParticipant:
            pass

        await client.promote_chat_member(
            chat_id,
            userbot_id,
            privileges=ChatPrivileges(can_delete_messages=True)
        )

    await status.edit("🧹 Deleting messages...")

    deleted = 0
    skipped = 0

    async for m in userbot.get_chat_history(chat_id):

        if m.id == status.id or m.id in MSG_IDS:
            continue
            
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

    if need_leave:
        await userbot.leave_chat(chat_id)

# ---------------- RUN ---------------- #

async def main():
    await userbot.start()
    await bot.start()
    log.info("Bot + Userbot started successfully (Pyrogram v2)")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
