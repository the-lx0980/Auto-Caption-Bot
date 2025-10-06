import os
import asyncio
import logging
from math import ceil

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ---------------- CONFIG ----------------
API_ID = int(os.getenv("API_ID", "17567701"))
API_HASH = os.getenv("API_HASH", "751e7a1469a1099fb3748c5ca755e918")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5326801541"))

# Channel & message to edit (as you specified)
STATUS_CHANNEL_ID = -100638737329  # channel id (integer)
STATUS_MESSAGE_ID = 345            # message id to edit

# Scheduler interval
CHECK_INTERVAL_MINUTES = 60  # 1 hour

# Page size for status page
PAGE_SIZE = 10

# ---------------- PROJECTS ----------------
# Add / update your projects here. Each project needs app_url + deploy_url.
PROJECTS = {
    "File Streamer": {
        "app_url": "https://file-strra.onrender.com",
        "deploy_url": "https://api.render.com/deploy/srv-cj8tea8eba7s73fvadu0?key=aZgM2q3f5pY"
    },
    "Video Stream": {
        "app_url": "https://video-strra.onrender.com",
        "deploy_url": "https://api.render.com/deploy/srv-cpuduhdjbks73efe7a0?key=PkNRRjskswGAo"
    },
    # add more projects as needed...
}

# In-memory UI state for pagination (single status message)
UI_STATE = {
    "page": 0  # current page shown on channel message
}

# Shared HTTP client (reuse)
HTTP_TIMEOUT = 10
http_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)

# Pyrogram client
app = Client("render_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# ---------------- Helpers ----------------
async def check_app_status(app_url: str) -> str:
    """Return status string: 'Online', 'Unstable (code)', or 'Down'"""
    try:
        r = await http_client.get(app_url)
        if r.status_code == 200:
            return "Online"
        else:
            return f"Unstable ({r.status_code})"
    except Exception as e:
        # Could be timeout, connection error etc.
        logging.debug(f"check_app_status error for {app_url}: {e}")
        return "Down"


async def trigger_render_deploy(deploy_url: str) -> str:
    """POST to Render deploy endpoint, return result message."""
    try:
        r = await http_client.post(deploy_url, timeout=30)
        if r.status_code == 200:
            return "Redeploy triggered ✅"
        else:
            return f"Deploy failed ({r.status_code})"
    except Exception as e:
        logging.exception("trigger_render_deploy error")
        return f"Error: {e}"


def build_status_page(project_names, statuses, page=0):
    """Return (text, keyboard) for the specified page index."""
    total = len(project_names)
    pages = max(1, ceil(total / PAGE_SIZE))
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    lines = []
    for idx, name in enumerate(project_names[start:end], start=start + 1):
        status = statuses.get(name, "Unknown")
        emoji = "🟢" if status == "Online" else ("🟡" if status.startswith("Unstable") else "🔴")
        lines.append(f"{idx}. <b>{name}</b> — {emoji} {status}")

    header = f"📊 <b>Project Status</b>\nChecked: <code>{asyncio.get_event_loop().time():.0f}</code>\n\n"
    body = "\n".join(lines) if lines else "No projects to display."
    footer = f"\n\nPage {page + 1}/{pages} • Total projects: {total}"

    # pagination buttons
    buttons = []
    row = []
    if page > 0:
        row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page:{page - 1}"))
    if page < pages - 1:
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page + 1}"))
    if row:
        buttons.append(row)

    # add manual actions
    buttons.append([InlineKeyboardButton("✅ Check All Now", callback_data="check_all")])
    keyboard = InlineKeyboardMarkup(buttons)

    return header + body + footer, keyboard


# ---------------- Core: Check all and update channel ----------------
async def check_all_and_update_channel(send_notifications: bool = True):
    """
    Check all projects, redeploy if Down, and update the channel message.
    send_notifications: if True, send owner notifications when redeploy happens.
    """
    logging.info("Running check_all_and_update_channel()")
    project_names = list(PROJECTS.keys())
    statuses = {}
    redeploy_results = {}

    # 1) Check statuses
    for name in project_names:
        app_url = PROJECTS[name]["app_url"]
        status = await check_app_status(app_url)
        statuses[name] = status

    # 2) Redeploy any that are Down
    for name, status in statuses.items():
        if status == "Down":
            deploy_url = PROJECTS[name]["deploy_url"]
            result = await trigger_render_deploy(deploy_url)
            redeploy_results[name] = result
            logging.info(f"Redeploy {name}: {result}")
            if send_notifications:
                try:
                    await app.send_message(OWNER_ID, f"⚠️ <b>{name}</b> was Down — {result}", parse_mode=ParseMode.HTML)
                except Exception as e:
                    logging.warning(f"Failed to notify owner for {name}: {e}")

    # 3) Build page content for current UI_STATE page and edit channel message
    text, keyboard = build_status_page(project_names, statuses, page=UI_STATE["page"])
    try:
        await app.edit_message_text(
            chat_id=STATUS_CHANNEL_ID,
            message_id=STATUS_MESSAGE_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        logging.info("Channel status message updated.")
    except Exception as e:
        logging.exception(f"Failed to edit channel status message: {e}")

    return statuses, redeploy_results


# ---------------- Scheduler ----------------
scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.add_job(lambda: asyncio.create_task(check_all_and_update_channel(send_notifications=True)),
                      "interval",
                      minutes=CHECK_INTERVAL_MINUTES,
                      id="auto_check_job",
                      replace_existing=True)
    scheduler.start()
    logging.info(f"Scheduler started: running every {CHECK_INTERVAL_MINUTES} minutes.")


# ---------------- Telegram handlers ----------------

# Start (owner only)
@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def cmd_start(_, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"menu:{name}")]
        for name in list(PROJECTS.keys())[:PAGE_SIZE]
    ] + [[InlineKeyboardButton("✅ Check All", callback_data="check_all")]])
    await message.reply_text("🤖 Render Manager Bot is active. Use the buttons below:", reply_markup=keyboard)


# Menu for a single project
@app.on_callback_query(filters.regex(r"^menu:(.+)"))
async def cb_menu(_, query):
    project_name = query.data.split(":", 1)[1]
    if project_name not in PROJECTS:
        await query.answer("Unknown project.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton("📊 Status", callback_data=f"status:{project_name}")],
        [InlineKeyboardButton("🔁 Redeploy", callback_data=f"deploy:{project_name}")],
        [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
    ]
    await query.message.edit_text(f"⚙️ <b>{project_name}</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))


# Per-project status
@app.on_callback_query(filters.regex(r"^status:(.+)"))
async def cb_status(_, query):
    project_name = query.data.split(":", 1)[1]
    data = PROJECTS.get(project_name)
    if not data:
        await query.answer("Unknown project.", show_alert=True)
        return

    status = await check_app_status(data["app_url"])
    text = f"<b>{project_name}</b>\nStatus: {status}"
    buttons = [
        [InlineKeyboardButton("🔁 Redeploy", callback_data=f"deploy:{project_name}")],
        [InlineKeyboardButton("🏠 Back", callback_data="back_menu")]
    ]
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))


# Deploy a project manually
@app.on_callback_query(filters.regex(r"^deploy:(.+)"))
async def cb_deploy(_, query):
    project_name = query.data.split(":", 1)[1]
    data = PROJECTS.get(project_name)
    if not data:
        await query.answer("Unknown project.", show_alert=True)
        return

    await query.message.edit_text(f"⏳ Redeploying <b>{project_name}</b>...", parse_mode=ParseMode.HTML)
    result = await trigger_render_deploy(data["deploy_url"])
    await query.message.edit_text(f"<b>{project_name}</b>\n{result}", parse_mode=ParseMode.HTML,
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back", callback_data="back_menu")]]))


# Back to main menu (simple)
@app.on_callback_query(filters.regex(r"^back_menu$"))
async def cb_back_menu(_, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"menu:{name}")]
        for name in list(PROJECTS.keys())[:PAGE_SIZE]
    ] + [[InlineKeyboardButton("✅ Check All", callback_data="check_all")]])
    await query.message.edit_text("📋 Projects", reply_markup=keyboard)


# Check all now (manual trigger)
@app.on_callback_query(filters.regex(r"^check_all$"))
async def cb_check_all(_, query):
    await query.message.edit_text("🔍 Checking all projects now... Please wait.", parse_mode=ParseMode.HTML)
    statuses, redeploys = await check_all_and_update_channel(send_notifications=True)
    # Build quick summary
    summary_lines = []
    for name, status in statuses.items():
        marker = "✅" if status == "Online" else ("🔁" if name in redeploys else "⚠️")
        summary_lines.append(f"{marker} <b>{name}</b> — {status}")
    text = "✅ <b>Manual Check Completed</b>\n\n" + "\n".join(summary_lines)
    await query.message.edit_text(text, parse_mode=ParseMode.HTML)


# Pagination handler for the status message
@app.on_callback_query(filters.regex(r"^page:(\d+)$"))
async def cb_page(_, query):
    new_page = int(query.data.split(":", 1)[1])
    UI_STATE["page"] = new_page
    # regenerate statuses quickly (don't redeploy in pagination)
    project_names = list(PROJECTS.keys())
    statuses = {}
    for name in project_names:
        statuses[name] = await check_app_status(PROJECTS[name]["app_url"])
    text, keyboard = build_status_page(project_names, statuses, page=new_page)
    try:
        await app.edit_message_text(
            chat_id=STATUS_CHANNEL_ID,
            message_id=STATUS_MESSAGE_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.exception("Failed to update page during pagination.")
    await query.answer()  # dismiss loader


# Block unauthorized users
@app.on_message(~filters.user(OWNER_ID))
async def block_unauth(_, msg):
    try:
        await msg.reply_text("🚫 You are not authorized to use this bot.")
    except Exception:
        pass


# ---------------- Startup / Shutdown ----------------
async def main():
    # start client
    await app.start()
    logging.info("Bot started.")
    # initialize scheduler
    start_scheduler()
    # do an initial check+update at startup (no notifications to owner)
    await check_all_and_update_channel(send_notifications=False)
    # keep running
    logging.info("Entering idle loop. Scheduler will run in background.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # close http client on shutdown
        try:
            asyncio.get_event_loop().run_until_complete(http_client.aclose())
        except Exception:
            pass
