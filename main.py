from pyrogram import Client, filters, enums
from os import environ
from openai import OpenAI

# ───────────────────────────────
# 🔧 CONFIG
# ───────────────────────────────
API_ID = 24456380
API_HASH = "fe4d4eb35510370ea1073fbcb36e1fcc"
BOT_TOKEN = environ.get("BOT_TOKEN")

FROM_CHAT_ID = -1001572995585   # Source channel
TO_CHAT_ID = -1001592628992     # Target channel




@app.on_message(filters.channel)
async def forward(bot, message):
    try:
        if not message.caption:
            return

        new_caption = await extract_caption_ai(message.caption)
        print(f"Old: {message.caption}\nNew: {new_caption}\n{'-'*40}")

        await bot.copy_message(
            chat_id=TO_CHAT_ID,
            from_chat_id=FROM_CHAT_ID,
            message_id=message.id,
            caption=new_caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )

    except Exception as e:
        print(f"Error forwarding: {e}")


# ───────────────────────────────
# 🔄 START COMMAND
# ───────────────────────────────
@app.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("✅ Bot is Alive and Ready!")


import requests

ANILIST_API_URL = "https://graphql.anilist.co"

async def generate_search_titles(title: str, season_number: int):
    """
    Generate all possible search variations automatically.
    Includes:
      - English variations (Season, Part, Arc, TV Season, Special Season, Final Season)
      - Different casing
      - Romaji / Native title
      - AniList synonyms
    """
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

    # Case variations
    variations = []
    for v in base_variations:
        variations += [v, v.lower(), v.upper(), v.title()]

    # Fetch romaji/native titles + synonyms from AniList
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

            # Add case variations
            for t in titles_to_add:
                variations += [t, t.lower(), t.upper(), t.title()]

    except requests.RequestException:
        pass

    # Remove duplicates while preserving order
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
                    # Clean output: avoid "Final Season Season N"
                    title_out = media['title']['romaji']
                    if "Final Season" in title_out:
                        print(f"✅ {title_out} ({year})")
                    else:
                        print(f"✅ {title_out} Season {season_number}: {year}")
                    return year
        except requests.RequestException:
            continue

    print(f"❌ No data found for '{title}' Season {season_number}")
    return None

# --------------------------
# Example usage
# --------------------------
anime_list = [
    ("Attack on Titan", 4),
    ("One Punch Man", 2),
    ("My Hero Academia", 5),
    ("Demon Slayer", 2),
    ("Jujutsu Kaisen", 1),
    ("Rent-A-Girlfriend", 4),
]

for anime, season in anime_list:
    get_anime_season_year(anime, season)
    
# ───────────────────────────────
# ▶️ RUN BOT
# ───────────────────────────────
print("🤖 Bot Started!")
app.run()
