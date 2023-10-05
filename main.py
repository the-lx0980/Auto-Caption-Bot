from pyrogram import Client, filters, enums

app = Client(
  'autocaption',
  api_id=6353248,
  api_hash='1346f958b9d917f0961f3e935329eeee',
  session_string="BQGb9AQAC5V8laNyrwshIL9_Z-Lx9aYFZBwdr58BH3Fgo6eGXjUonmIyfFMAUeNWHuVcDjuMWVMRvGhQCQh3Ab2BMPUYnAOu_ZAvdyg4SJXC1r2IV5Ot7XtEFmImYGKvKGUkPR0_kHGxEcwftFYy7y7fxtG1a8R9_VCTrzJVHePIfRyTkEy3jkUKWH2Ce12ZaDrulqTNaEZR8NtZ8pTGNyg-9kKH5ahTwS8N5MBCje7RMzLvj0-zCpJAgn3tZPbGk3MLNJR1gY7qQKiR7Qm7KnvyuoKG_nTDMd7z3Yvg2Fj01XWu9Kqm5r4y8v9wWR12CNBtl1B-2FLdogpQtTgyPXGrQwMbZAAAAAFM4O0NAA"
)

@app.on_message(filters.command('start'))
async def start(bot, update):
    await update.reply("Hello, I'm Auto Caption Bot")

@app.on_message((filters.video | filters.document) & filters.channel)
async def autocaption(bot, update):
    await bot.edit_media_caption(
        caption='This Caption From Bot',
        message_id=update.id,
        chat_id=update.chat.id,
        parse_mode=enums.ParseMode.MARKDOWN
    )

app.run()
