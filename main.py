import os
import asyncio

import discord
from discord.ext import commands

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TOKEN = os.environ.get("TOKEN")
GUILD = os.environ.get("GUILD")
PREFIX = os.environ.get("PREFIX")

class Bot(commands.Bot):
   def __init__(self) -> None:
      intents = discord.Intents.default()
      intents.message_content = True
      intents.voice_states = True

      super().__init__(intents=intents, command_prefix=commands.when_mentioned_or(PREFIX))
   
   async def on_ready(self):
      print('[BOT] Okay I\'m ready.')

   async def load_extensions(self):
      for commandfile in os.listdir('./commands'):
         if commandfile.endswith('.py'):
            await bot.load_extension(f'commands.{commandfile[:-3]}')
      print('[BOT] All additional commands load!')

   async def mainSetup(self):
      async with bot:
         await self.load_extensions()
         await self.start(TOKEN)

bot = Bot()

if __name__ == "__main__":
   asyncio.run(bot.mainSetup())
else:
   raise Exception("You trying start main file like a additional")
