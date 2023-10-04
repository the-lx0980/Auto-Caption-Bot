from pyrogram import Client, filters, enums

app = Client(
  'autocaption',
  api_id=6353248,
  api_hash='1346f958b9d917f0961f3e935329eeee',
  bot_token='6285956621:AAF16zJce7vXr3wukHJDO9qOYpXQ-AcSInU'
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
