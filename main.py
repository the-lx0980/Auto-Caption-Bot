import os
import httpx
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

API_ID = 17567701 #int(os.getenv("API_ID"))
API_HASH = "751e7a1469a1099fb3748c5ca755e918" #os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5326801541"))

#https://api.render.com/deploy/ srv-cj8tea8eba7s73fvadu0 ?key =aZgM2q3f5pY
# ✅ Multiple Render Projects (each with its own Render API key)

PROJECTS = {
    "WebXzone": {
        "service_id": "srv-cj8tea8eba7s73fvadu0",
        "api_key": "aZgM2q3f5pY",
    },
    "Video Host": {
        "service_id": "srv-cxyz123abc456",
        "api_key": "PHabc123xyz789",
    },
    "API Server": {
        "service_id": "srv-c987def654ghi",
        "api_key": "PH654xyz987pqr",
    },
    # ➕ Add more projects below
}

app = Client(
    "multi_render_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML   # Use enum-based parse mode ✅
)


# --- Helper: Trigger Render deploy ---
async def trigger_render_deploy(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url) as resp:
                if resp.status == 200:
                    return "✅ Successfully triggered redeploy on Render!"
                else:
                    text = await resp.text()
                    return f"❌ Failed ({resp.status}): {text}"
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
        reply_markup=keyboard
    )


# --- Inline button handler ---
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

    # Trigger deploy
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


# --- Back to menu button ---
@app.on_callback_query(filters.regex("^back_menu$"))
async def back_menu(_, query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"deploy:{name}")]
        for name in PROJECTS.keys()
    ])
    await query.message.edit_text(
        "📋 <b>Render Projects</b>\nSelect one to redeploy:",
        reply_markup=keyboard
    )


# --- Run the bot ---
print("✅ Bot is running...")
app.run()
    if not data.startswith("deploy:"):
        await query.answer("Invalid data.", show_alert=True)
        return

    project_name = data.split(":", 1)[1]
    project = PROJECTS.get(project_name)

    if not project:
        await query.message.edit_text("❌ Unknown project.")
        return

    service_id = project["service_id"]
    api_key = project["api_key"]

    await query.message.edit_text(f"⏳ Redeploying *{project_name}* ...", parse_mode="markdown")

    result = await trigger_render_deploy(service_id, api_key)
    await query.message.edit_text(f"**{project_name}**\n{result}", parse_mode="markdown")

# Block unauthorized users
@app.on_message(~filters.user(OWNER_ID))
async def unauthorized(_, msg):
    await msg.reply_text("🚫 You are not authorized to use this bot.")

if __name__ == "__main__":
    print("🤖 Multi-account Render bot started!")
    app.run()
