# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
import asyncio
import telegram

BOT_TOKEN = '5690693191:AAHBTNpQDPqtJaWeHM5I9NAotBY4JZuGkaA'  #testbot_151122_bot
# BOT_TOKEN = '5825256749:AAHYwto9Qb1UufQvne-52C9mB1-rmM2hgD8'  #@x_bot_151222_bot

async def main():
    bot = telegram.Bot(
        token=BOT_TOKEN, 
        base_url='http://localhost:8081/bot',
        local_mode=True,
        base_file_url='http://localhost:8081/file/bot'
        )
    
    async with bot:
        print(await bot.get_me())
        print(await bot.get_updates())
        #file_id = 'BQACAgUAAxkBAAIDV2VDkqv70KZ3ZPhwI7pPw6tebZBiAAKmDwACVqkYVtuJp-KuvCPeMAQ'  #file_name='dmtx-1per4.pdf'
        # file_id='BQACAgUAAxkBAAIDWGVDlRmCsaDi6nm-KCXhC316wHDxAAKpDwACVqkYVl8wzIXCNrhCMAQ'   # Binder1
        # f = await bot.get_file(file_id=file_id)
        # await f.download_to_drive(
        #     read_timeout=1000.0
        #     )
        # print(await bot.log_out())


if __name__ == '__main__':
    asyncio.run(main())
    