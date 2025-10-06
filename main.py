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

app = Client("multi_render_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to trigger Render redeploy
async def trigger_render_deploy(service_id: str, api_key: str) -> str:
    url = f"https://api.render.com/deploy/{service_id}?key={api_key}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(url)
            if r.status_code in [200, 201, 202]:
                return f"✅ Deploy started for `{service_id}` (HTTP {r.status_code})"
            else:
                return f"⚠️ Failed (HTTP {r.status_code})\nResponse: {r.text}"
        except Exception as e:
            return f"❌ Error: {e}"

# /start
@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start(_, msg):
    await msg.reply_text(
        "👋 Welcome! This bot can redeploy your multiple Render projects.\nUse /redeploy to view all."
    )

# /redeploy command → show all projects
@app.on_message(filters.command("redeploy") & filters.user(OWNER_ID))
async def redeploy_list(_, msg):
    buttons = []
    for name, info in PROJECTS.items():
        buttons.append([
            InlineKeyboardButton(f"🚀 {name}", callback_data=f"deploy:{name}")
        ])
    await msg.reply_text(
        "Select a project to redeploy 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Handle button press
@app.on_callback_query(filters.user(OWNER_ID))
async def deploy_button(_, query):
    data = query.data
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
