import os
import asyncio
import httpx
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "17567701"))
API_HASH = os.getenv("API_HASH", "751e7a1469a1099fb3748c5ca755e918")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5326801541"))

PROJECTS = {
    "File Streamer": "https://api.render.com/deploy/srv-cj8tea8eba7s73fvadu0?key=aZgM2q3f5pY",
    "Video Stream": "https://api.render.com/deploy/srv-cpuduhdjbks73efe7a0?key=PkNRRjskswGAo",
}

app = Client(
    "multi_render_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- Trigger Render Deploy using httpx ---
async def trigger_render_deploy(url: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url)
            if resp.status_code == 200:
                return "✅ Successfully triggered redeploy!"
            else:
                return f"❌ Failed ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"⚠️ Error: {e}"

# --- /start command ---
@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(_, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"deploy:{name}")]
        for name in PROJECTS.keys()
    ])
    await message.reply_text(
        "👋 <b>Welcome!</b>\nChoose a project below to redeploy on Render:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# --- Deploy button ---
@app.on_callback_query(filters.regex(r"^deploy:(.+)"))
async def deploy_button(_, query):
    project_name = query.data.split(":", 1)[1]
    deploy_url = PROJECTS.get(project_name)

    if not deploy_url:
        await query.answer("❌ Project not found!", show_alert=True)
        return

    try:
        await query.message.edit_text(
            f"⏳ Redeploying <b>{project_name}</b> ...",
            parse_mode=ParseMode.HTML
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"Edit error: {e}")

    result = await trigger_render_deploy(deploy_url)

    try:
        await query.message.edit_text(
            f"<b>{project_name}</b>\n\n{result}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Redeploy Again", callback_data=f"deploy:{project_name}")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"Message update error: {e}")

# --- Back to menu ---
@app.on_callback_query(filters.regex("^back_menu$"))
async def back_menu(_, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"deploy:{name}")]
        for name in PROJECTS.keys()
    ])
    await query.message.edit_text(
        "📋 <b>Render Projects</b>\nSelect one to redeploy:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# --- Block unauthorized users ---
@app.on_message(~filters.user(OWNER_ID))
async def unauthorized(_, msg):
    await msg.reply_text("🚫 You are not authorized to use this bot.")

# --- Run bot ---
if __name__ == "__main__":
    print("🤖 Multi-account Render bot started!")
    app.run()
