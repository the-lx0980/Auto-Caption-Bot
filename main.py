from pyrogram import Client, filters, enums
from os import environ

app_id = 24456380
api_hash = "fe4d4eb35510370ea1073fbcb36e1fcc"
bot_token = environ.get('BOT_TOKEN')
chat_id = 
from_chat_id = 

app = Client(    
    name='webxzonebot',
    api_id=app_id,
    api_hash=api_hash,
    bot_token=bot_token
)

@app.on_message(filters.channel)
async def forward(bot, message):
    try:
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            caption=f'**{message.caption}**',
            message_id=message.id,
            parse_mode=enums.ParseMode.MARKDOWN            
        )
    except Exception as e:
        print(f'{e}')

@app.on_message(filters.command('start'))
async def start(bot, message):
    await message.reply('Alive')

print('Bot Started!')
app()
