import logging
import requests
from pyrogram import Client, filters, enums, Message
from os import environ
import asyncio
import logging
from userbot import userbot
from pyrogram.errors import UserAlreadyParticipant, FloodWait
from pyrogram.enums import ChatType, ChatMemberStatus


API_ID = 24456380
API_HASH = "fe4d4eb35510370ea1073fbcb36e1fcc"
BOT_TOKEN = environ.get("BOT_TOKEN")


app = Client("webxzonebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@Stark.cmd("delall", description="Delete all messages in a group/channel")
async def main_func(bot: Stark, msg: Message):

    # Ignore private chats
    if msg.chat.type == ChatType.PRIVATE:
        return

    # Admin check (for groups)
    if msg.chat.type != ChatType.CHANNEL:
        user = await bot.get_chat_member(msg.chat.id, msg.from_user.id)

        if user.status not in (
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR
        ):
            return

        if not user.privileges or not user.privileges.can_delete_messages:
            await msg.react("You don't have `CanDeleteMessages` right.")
            return

    # Bot admin check
    bot_id = (await bot.get_me()).id
    cm = await bot.get_chat_member(msg.chat.id, bot_id)

    if cm.status != ChatMemberStatus.ADMINISTRATOR:
        await msg.react("I'm not admin here!")
        return

    if not cm.privileges or not cm.privileges.can_delete_messages:
        await msg.react("I need delete messages permission.")
        return

    if not cm.privileges.can_promote_members:
        await msg.react("I need promote members permission.")
        return

    # Join via userbot
    link = (await bot.get_chat(msg.chat.id)).invite_link
    try:
        await userbot.join_chat(link)
    except UserAlreadyParticipant:
        pass

    # Promote userbot
    userbot_id = (await userbot.get_me()).id
    await bot.promote_chat_member(
        msg.chat.id,
        userbot_id,
        can_delete_messages=True
    )

    # Collect message IDs
    message_ids = []

    while True:
        try:
            async for m in userbot.get_chat_history(msg.chat.id):
                message_ids.append(m.id)
            break
        except FloodWait as e:
            await msg.react(
                f"FloodWait: wait {e.value} seconds.\nTelegram restriction."
            )
            await asyncio.sleep(e.value)

    # Split into chunks of 100
    chunks = [
        message_ids[i:i + 100]
        for i in range(0, len(message_ids), 100)
    ]

    status = await msg.reply("🧹 Deleting all messages...")

    # Delete messages
    for chunk in chunks:
        while True:
            try:
                await userbot.delete_messages(msg.chat.id, chunk)
                break
            except FloodWait as e:
                await asyncio.sleep(e.value)
                Stark.log(str(e), logging.WARNING)

    await status.delete()
    await msg.react("✅ Successfully deleted everything!")
    await userbot.leave_chat(msg.chat.id)

app.run() 
