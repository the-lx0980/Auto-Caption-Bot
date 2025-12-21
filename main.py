import asyncio
import json
import time
import logging
from os import getenv

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, ChatPrivileges

# ---------------- CONFIG ---------------- #

API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
BOT_TOKEN = getenv("BOT_TOKEN")
USERBOT_STRING = getenv("USERBOT_STRING")

MSG_ID = 25864  # message ID to protect

WHITELIST_USERS = {
    6804133304,
    6446224566
}

PROGRESS_FILE = "progress.json"
CANCEL_TASKS = set()

# ---------------- LOGGING ---------------- #

logging.basicConfig(level=logging.INFO)
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

# ---------------- HELPERS ---------------- #

def progress_bar(percent):
    total = 20
    filled = int((percent / 100) * total)
    return "▓" * filled + "░" * (total - filled)

def load_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

def format_eta(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"

# ---------------- CANCEL COMMAND ---------------- #

@bot.on_message(filters.command("cancel") & filters.group)
async def cancel_handler(_, msg: Message):
    CANCEL_TASKS.add(msg.chat.id)
    await msg.reply("⛔ Deletion cancelled")

# ---------------- DELETE COMMAND ---------------- #

@bot.on_message(filters.command("delall") & filters.group)
async def delete_all_handler(client: Client, msg: Message):

    chat_id = msg.chat.id

    # -------- ADMIN CHECK -------- #

    member = await client.get_chat_member(chat_id, msg.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await msg.reply("❌ Admin only")

    bot_member = await client.get_chat_member(chat_id, (await client.get_me()).id)
    priv = bot_member.privileges

    if not priv or not priv.can_delete_messages:
        return await msg.reply("❌ Bot needs delete permission")

    status = await msg.reply("🧹 Preparing deletion...")

    # -------- USERBOT SETUP -------- #

    userbot_id = (await userbot.get_me()).id
    need_leave = False
    need_demote = False

    try:
        ub_member = await client.get_chat_member(chat_id, userbot_id)
        if ub_member.status != ChatMemberStatus.ADMINISTRATOR:
            await client.promote_chat_member(
                chat_id,
                userbot_id,
                privileges=ChatPrivileges(can_delete_messages=True)
            )
            need_demote = True
    except UserNotParticipant:
        invite = await client.create_chat_invite_link(chat_id)
        await userbot.join_chat(invite.invite_link)
        await client.promote_chat_member(
            chat_id,
            userbot_id,
            privileges=ChatPrivileges(can_delete_messages=True)
        )
        need_leave = True

    # -------- LOAD PROGRESS -------- #

    progress = load_progress().get(str(chat_id), {})
    last_id = progress.get("last_id", 0)
    user_stats = progress.get("users", {})

    # -------- COUNT TOTAL -------- #

    total = 0
    async for _ in userbot.get_chat_history(chat_id):
        total += 1

    start_time = time.time()
    deleted = 0
    skipped = 0
    last_percent = -1

    # -------- DELETE LOOP (NO BATCH) -------- #

    async for m in userbot.get_chat_history(chat_id):

        if chat_id in CANCEL_TASKS:
            await status.edit("⛔ Cancelled")
            break

        if m.id <= last_id:
            continue

        if m.id in (status.id, MSG_ID):
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

        uid = str(m.from_user.id)
        user_stats[uid] = user_stats.get(uid, 0) + 1

        if deleted and deleted % 100 == 0:
            percent = int((deleted / total) * 100)
            if percent >= last_percent + 5:
                last_percent = percent
                elapsed = time.time() - start_time
                speed = deleted / elapsed if elapsed else 0
                eta = (total - deleted) / speed if speed else 0

                await status.edit(
                    f"🧹 Deleting...\n\n"
                    f"{progress_bar(percent)} {percent}%\n"
                    f"🗑 Deleted: {deleted}\n"
                    f"⏭ Skipped: {skipped}\n"
                    f"⏳ ETA: {format_eta(eta)}"
                )

        save_progress({
            str(chat_id): {
                "last_id": m.id,
                "users": user_stats
            }
        })

    # -------- FINAL -------- #

    await status.edit(
        f"✅ Done\n\n"
        f"🗑 Deleted: {deleted}\n"
        f"⏭ Skipped: {skipped}"
    )

    # -------- CLEANUP -------- #

    if need_demote:
        await client.promote_chat_member(chat_id, userbot_id, ChatPrivileges())

    if need_leave:
        await userbot.leave_chat(chat_id)

# ---------------- RUN ---------------- #

async def main():
    await userbot.start()
    await bot.start()
    await asyncio.Event().wait()

bot.run(main())
