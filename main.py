import logging
import requests
from pyrogram import Client, filters, enums
from os import environ
# ───────────────────────────────
# 🔧 CONFIG
# ───────────────────────────────
API_ID = 24456380
API_HASH = "fe4d4eb35510370ea1073fbcb36e1fcc"
BOT_TOKEN = environ.get("BOT_TOKEN")

FROM_CHAT_ID = -1001572995585   # Source channel
TO_CHAT_ID = -1001592628992     # Target channel

app = Client("webxzonebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ───────────────────────────────
# 📌 Logging Setup
# ───────────────────────────────
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.on_message(filters.channel)
async def forward(bot, message):
    try:
        if not message.caption:
            return
        await bot.copy_message(
            chat_id=TO_CHAT_ID,
            from_chat_id=FROM_CHAT_ID,
            message_id=message.id,
            caption=message.caption,  # aap new_caption use kar rahe the, ensure defined
            parse_mode=enums.ParseMode.MARKDOWN
        )
        logger.info(f"Message forwarded from {FROM_CHAT_ID} to {TO_CHAT_ID}")
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")


@app.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("✅ Bot is Alive and Ready!")
    logger.info(f"/start command received from {message.from_user.id}")


ANILIST_API_URL = "https://graphql.anilist.co"

def generate_search_titles(title: str, season_number: int):
    base_variations = [
        f"{title} Season {season_number}",
        f"{title} Part {season_number}",
        f"{title} {season_number}",
        f"{title} {season_number}th Season",
        f"{title} Final Season",
        f"{title} Arc {season_number}",
        f"{title} TV Season {season_number}",
        f"{title} Special Season {season_number}",
    ]

    variations = []
    for v in base_variations:
        variations += [v, v.lower(), v.upper(), v.title()]

    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        title { romaji native }
        synonyms
      }
    }
    '''
    variables = {"search": title}
    try:
        response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        data = response.json().get("data", {}).get("Media", {})
        if data:
            titles_to_add = []
            romaji = data.get("title", {}).get("romaji")
            native = data.get("title", {}).get("native")
            synonyms = data.get("synonyms", [])

            for t in [romaji, native] + synonyms:
                if t:
                    titles_to_add += [
                        f"{t} Season {season_number}",
                        f"{t} Part {season_number}",
                        f"{t} {season_number}",
                        f"{t} Final Season",
                        f"{t} Arc {season_number}",
                        f"{t} TV Season {season_number}",
                        f"{t} Special Season {season_number}"
                    ]
            for t in titles_to_add:
                variations += [t, t.lower(), t.upper(), t.title()]

    except requests.RequestException as e:
        logger.warning(f"Error fetching AniList titles for '{title}': {e}")

    return list(dict.fromkeys(variations))


def get_anime_season_year(title: str, season_number: int) -> int | None:
    search_titles = generate_search_titles(title, season_number)
    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        title { romaji }
        startDate { year }
      }
    }
    '''
    for search_title in search_titles:
        variables = {"search": search_title}
        try:
            response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
            response.raise_for_status()
            media = response.json().get("data", {}).get("Media")
            if media:
                year = media.get("startDate", {}).get("year")
                if year:
                    title_out = media['title']['romaji']
                    if "Final Season" in title_out:
                        logger.info(f"✅ {title_out} ({year})")
                    else:
                        logger.info(f"✅ {title_out} Season {season_number}: {year}")
                    return year
        except requests.RequestException:
            continue

    logger.warning(f"❌ No data found for '{title}' Season {season_number}")
    return None


anime_list = [
    ("Attack on Titan", 4),
    ("One Piece", 26),
    ("Naruto Shippuden", 21),
    ("Boruto: Naruto Next Generations", 3),
    ("One Punch Man", 3),
    ("My Hero Academia", 6),
    ("Demon Slayer", 3),
    ("Jujutsu Kaisen", 2),
    ("Tokyo Revengers", 2),
    ("Spy x Family", 2),
    ("Chainsaw Man", 1),
    ("Bleach", 17),
    ("Dragon Ball Super", 6),
    ("Rent-A-Girlfriend", 4),
    ("Black Clover", 5),
    ("Re:Zero − Starting Life in Another World", 3),
    ("The Rising of the Shield Hero", 3),
    ("Sword Art Online", 4),
    ("Fullmetal Alchemist: Brotherhood", 1),
    ("Code Geass: Lelouch of the Rebellion", 2),
]

for anime, season in anime_list:
    get_anime_season_year(anime, season)

logger.info("🤖 Bot Started!")
app.run()
