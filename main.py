from pyrogram import Client, filters, enums

app = Client(
  'autocaption',
  api_id = v,
  api_hash = '',
  bot_token = ''
)  

@app.on_message(filters.command('start'))
async def start(bot, update):
    await update.reply("Hello I'm Auto Caption Bot")
    
@app.on_message((filters.video | filters.document) & filters.channel)
async def autocaption(bot, update):
    await bot.edit_media_caption(
        caption = 'This Caption From Bot',
        message_id = update.id,
        chat_id = update.chat.id,
        patse_mode = enums.ParseMode.MARKDOWN
    )

app.run()
