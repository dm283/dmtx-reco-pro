# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
import sys, os, asyncio, telegram, configparser
from pathlib import Path

config = configparser.ConfigParser()
config_file = os.path.join(Path(__file__).resolve().parent, 'config.ini')
if os.path.exists(config_file):
  config.read(config_file, encoding='utf-8')
else:
  print("error! config file doesn't exist"); sys.exit()

BOT_TOKEN = config['telegram_bot']['bot_token']
TELEGRAM_SERVER = config['telegram_bot']['telegram_server']

async def main():
    if TELEGRAM_SERVER == 'local':
        bot = telegram.Bot(
            token=BOT_TOKEN, 
            base_url='http://localhost:8081/bot',
            local_mode=True,
            base_file_url='http://localhost:8081/file/bot'
            )
    elif TELEGRAM_SERVER == 'official':
       bot = telegram.Bot(token=BOT_TOKEN)
            

    async with bot:
        print(await bot.get_me())
        print(await bot.get_updates())

        file_id=''  # get from 'get_updates()' it after sent file to bot
        # f = await bot.get_file(file_id=file_id)
        # await f.download_to_drive(
        #     read_timeout=2000.0
        #     )

        # print(await bot.log_out()) !!! # for switch bot from official server to local server


if __name__ == '__main__':
    asyncio.run(main())
    