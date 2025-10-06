import os
import asyncio
import logging
from math import ceil
from datetime import datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from projects import PROJECTS

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ---------------- CONFIG ----------------
API_ID = int(os.getenv("API_ID", "17567701"))
API_HASH = os.getenv("API_HASH", "751e7a1469a1099fb3748c5ca755e918")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5326801541"))

STATUS_CHANNEL_ID = -1001572995585
STATUS_MESSAGE_ID = 22
CHECK_INTERVAL_MINUTES = 1
PAGE_SIZE = 10


# ---------------- STATE ----------------
UI_STATE = {"page": 0}  # PM pagination
HTTP_TIMEOUT = 10
http_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
app = Client("render_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- HELPERS ----------------
async def check_app_status(app_url: str) -> str:
    try:
        r = await http_client.get(app_url)
        if r.status_code == 200:
            return "Online"
        else:
            return f"Unstable ({r.status_code})"
    except Exception:
        return "Down"

async def trigger_render_deploy(deploy_url: str) -> str:
    try:
        r = await http_client.post(deploy_url, timeout=30)
        if r.status_code == 200:
            return "Redeploy triggered ✅"
        else:
            return f"Deploy failed ({r.status_code})"
    except Exception as e:
        return f"Error: {e}"

def build_status_page(project_names, statuses, page=0, for_channel=False):
    total = len(project_names)
    pages = max(1, ceil(total / PAGE_SIZE))
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    lines = []
    buttons = []

    # Project list section
    for idx, name in enumerate(project_names[start:end], start=start + 1):
        status = statuses.get(name, "Unknown")
        emoji = "🟢" if status == "Online" else ("🟡" if status.startswith("Unstable") else "🔴")
        lines.append(f"{idx}. <b>{name}</b> — {emoji} {status}")
        # Add a clickable button for this project
        buttons.append([InlineKeyboardButton(f"{emoji} {name}", callback_data=f"menu:{name}")])

    header = f"📊 <b>Project Status</b>\nLast checked: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n"
    body = "\n".join(lines) if lines else "No projects to display."
    footer = f"\n\nPage {page + 1}/{pages} • Total projects: {total}"
    text = header + body + footer

    if for_channel:
        # Channel message has no buttons
        return text, None

    # Pagination buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page:{page - 1}"))
    if page < pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    # Check all button
    buttons.append([InlineKeyboardButton("✅ Check All Now", callback_data="check_all")])

    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard

# ---------------- CORE ----------------
async def check_all_and_update_channel(send_notifications: bool = True):
    logging.info("Running check_all_and_update_channel()")
    project_names = list(PROJECTS.keys())
    statuses = {}
    redeploy_results = {}

    for name in project_names:
        statuses[name] = await check_app_status(PROJECTS[name]["app_url"])

    for name, status in statuses.items():
        if status == "Down":
            result = await trigger_render_deploy(PROJECTS[name]["deploy_url"])
            redeploy_results[name] = result
            if send_notifications:
                try:
                    await app.send_message(OWNER_ID, f"⚠️ <b>{name}</b> was Down — {result}", parse_mode=ParseMode.HTML)
                except Exception:
                    pass

    # Channel update (plain text)
    text, _ = build_status_page(project_names, statuses, for_channel=True)
    try:
        await app.edit_message_text(
            chat_id=STATUS_CHANNEL_ID,
            message_id=STATUS_MESSAGE_ID,
            text=text,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    return statuses, redeploy_results

# ---------------- SCHEDULER ----------------
scheduler = AsyncIOScheduler()
def start_scheduler():
    scheduler.add_job(lambda: asyncio.create_task(check_all_and_update_channel(send_notifications=True)),
                      "interval", minutes=CHECK_INTERVAL_MINUTES, id="auto_check_job", replace_existing=True)
    scheduler.start()

# ---------------- TELEGRAM HANDLERS ----------------
@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def cmd_start(_, message):
    project_names = list(PROJECTS.keys())
    statuses = {name:"Unknown" for name in project_names}
    text, keyboard = build_status_page(project_names, statuses, page=0)
    await message.reply_text("🤖 Render Manager Bot is active. Use buttons below:", reply_markup=keyboard, parse_mode=ParseMode.HTML)

# Pagination in PM
@app.on_callback_query(filters.regex(r"^page:(\d+)$"))
async def cb_page(_, query):
    new_page = int(query.data.split(":", 1)[1])
    UI_STATE["page"] = new_page
    project_names = list(PROJECTS.keys())
    statuses = {name: await check_app_status(PROJECTS[name]["app_url"]) for name in project_names}
    text, keyboard = build_status_page(project_names, statuses, page=new_page)
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await query.answer()

# Manual Check All in PM
@app.on_callback_query(filters.regex(r"^check_all$"))
async def cb_check_all(_, query):
    await query.message.edit_text("🔍 Checking all projects... Please wait.", parse_mode=ParseMode.HTML)
    statuses, redeploys = await check_all_and_update_channel(send_notifications=True)
    summary_lines = []
    for name, status in statuses.items():
        marker = "✅" if status=="Online" else ("🔁" if name in redeploys else "⚠️")
        summary_lines.append(f"{marker} <b>{name}</b> — {status}")
    text = "✅ <b>Manual Check Completed</b>\n\n" + "\n".join(summary_lines)
    keyboard = build_status_page(list(PROJECTS.keys()), statuses, page=UI_STATE["page"])[1]
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# Per-project menu in PM
@app.on_callback_query(filters.regex(r"^menu:(.+)$"))
async def cb_menu(_, query):
    project_name = query.data.split(":",1)[1]
    if project_name not in PROJECTS:
        await query.answer("Unknown project.", show_alert=True)
        return
    buttons = [
        [InlineKeyboardButton("📊 Status", callback_data=f"status:{project_name}")],
        [InlineKeyboardButton("🔁 Redeploy", callback_data=f"deploy:{project_name}")],
        [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
    ]
    await query.message.edit_text(f"⚙️ <b>{project_name}</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^status:(.+)$"))
async def cb_status(_, query):
    project_name = query.data.split(":",1)[1]
    if project_name not in PROJECTS:
        await query.answer("Unknown project.", show_alert=True)
        return
    status = await check_app_status(PROJECTS[project_name]["app_url"])
    text = f"<b>{project_name}</b>\nStatus: {status}"
    buttons = [
        [InlineKeyboardButton("🔁 Redeploy", callback_data=f"deploy:{project_name}")],
        [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^deploy:(.+)$"))
async def cb_deploy(_, query):
    project_name = query.data.split(":",1)[1]
    if project_name not in PROJECTS:
        await query.answer("Unknown project.", show_alert=True)
        return
    await query.message.edit_text(f"⏳ Redeploying <b>{project_name}</b>...", parse_mode=ParseMode.HTML)
    result = await trigger_render_deploy(PROJECTS[project_name]["deploy_url"])
    await query.message.edit_text(f"<b>{project_name}</b>\n{result}", parse_mode=ParseMode.HTML,
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back", callback_data="back_menu")]]))

@app.on_callback_query(filters.regex(r"^back_menu$"))
async def cb_back_menu(_, query):
    project_names = list(PROJECTS.keys())
    statuses = {name:"Unknown" for name in project_names}
    text, keyboard = build_status_page(project_names, statuses, page=UI_STATE["page"])
    await query.message.edit_text("📋 Projects", reply_markup=keyboard)

# Block unauthorized users
@app.on_message(~filters.user(OWNER_ID))
async def block_unauth(_, msg):
    try:
        await msg.reply_text("🚫 You are not authorized to use this bot.")
    except Exception:
        pass

# ---------------- STARTUP ----------------
async def main():
    await app.start()
    logging.info("Bot started.")
    start_scheduler()
    await check_all_and_update_channel(send_notifications=False)
    logging.info("Entering idle loop.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        try:
            asyncio.get_event_loop().run_until_complete(http_client.aclose())
        except Exception:
            pass
