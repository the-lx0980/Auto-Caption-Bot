# v3
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
    "File Streamer": {
        "deploy_url": "https://api.render.com/deploy/srv-cj8tea8eba7s73fvadu0?key=aZgM2q3f5pY",
        "app_url": "https://webxzonebot.onrender.com"
    },
    "Channel Clone": {
        "deploy_url": "https://api.render.com/deploy/srv-cs7j8lbv2p9s73f3dksg?key=Midzpimsd88",
        "app_url": "https://the-cloner-boy-cx2q.onrender.com"
    }
}
    
app = Client(
    "multi_render_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---- Helper: Trigger Deploy ----
async def trigger_render_deploy(url: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url)
            if resp.status_code == 200:
                return "✅ Redeploy triggered successfully!"
            return f"❌ Failed ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"⚠️ Error: {e}"

# ---- Helper: Check App Status ----
async def check_app_status(app_url: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(app_url)
            if resp.status_code == 200:
                return "🟢 Online"
            else:
                return f"🟡 Unstable ({resp.status_code})"
        except Exception:
            return "🔴 Down / Sleeping"

# ---- /start ----
@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(_, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"menu:{name}")]
        for name in PROJECTS.keys()
    ] + [[InlineKeyboardButton("✅ Check All", callback_data="check_all")]])
    await message.reply_text(
        "👋 <b>Welcome!</b>\nChoose a project below to manage:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# ---- Project Menu ----
@app.on_callback_query(filters.regex(r"^menu:(.+)"))
async def project_menu(_, query):
    project_name = query.data.split(":", 1)[1]
    buttons = [
        [InlineKeyboardButton("📊 Status", callback_data=f"status:{project_name}")],
        [InlineKeyboardButton("🔁 Redeploy", callback_data=f"deploy:{project_name}")],
        [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
    ]
    await query.message.edit_text(
        f"⚙️ <b>{project_name}</b> options:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

# ---- Check Status ----
@app.on_callback_query(filters.regex(r"^status:(.+)"))
async def check_status(_, query):
    project_name = query.data.split(":", 1)[1]
    app_url = PROJECTS[project_name]["app_url"]

    status = await check_app_status(app_url)
    await query.message.edit_text(
        f"<b>{project_name}</b>\nStatus: {status}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Redeploy", callback_data=f"deploy:{project_name}")],
            [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
        ]),
        parse_mode=ParseMode.HTML
    )

# ---- Deploy ----
@app.on_callback_query(filters.regex(r"^deploy:(.+)"))
async def deploy_project(_, query):
    project_name = query.data.split(":", 1)[1]
    deploy_url = PROJECTS[project_name]["deploy_url"]

    await query.message.edit_text(
        f"⏳ Redeploying <b>{project_name}</b>...",
        parse_mode=ParseMode.HTML
    )

    result = await trigger_render_deploy(deploy_url)

    await query.message.edit_text(
        f"<b>{project_name}</b>\n{result}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
        ]),
        parse_mode=ParseMode.HTML
    )

# ---- Check All ----
@app.on_callback_query(filters.regex("^check_all$"))
async def check_all(_, query):
    msg = "🔍 <b>Checking all projects...</b>\n\n"
    await query.message.edit_text(msg, parse_mode=ParseMode.HTML)

    report = ""
    for name, data in PROJECTS.items():
        status = await check_app_status(data["app_url"])
        report += f"• <b>{name}</b>: {status}\n"
        if "Down" in status or "Sleeping" in status:
            deploy_result = await trigger_render_deploy(data["deploy_url"])
            report += f"↪️ Redeploy: {deploy_result}\n\n"
        else:
            report += "\n"

    await query.message.edit_text(
        f"✅ <b>Check Completed!</b>\n\n{report}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back", callback_data="back_menu")]])
    )

# ---- Back Menu ----
@app.on_callback_query(filters.regex("^back_menu$"))
async def back_menu(_, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"menu:{name}")]
        for name in PROJECTS.keys()
    ] + [[InlineKeyboardButton("✅ Check All", callback_data="check_all")]])
    await query.message.edit_text(
        "📋 <b>Render Projects</b>\nSelect one:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# ---- Unauthorized ----
@app.on_message(~filters.user(OWNER_ID))
async def unauthorized(_, msg):
    await msg.reply_text("🚫 You are not authorized to use this bot.")

# ---- Run ----
if __name__ == "__main__":
    print("🤖 Render Manager Bot started!")
    app.run()
