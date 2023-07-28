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

bot = Bot()

async def load_extensions():
   for commandfile in os.listdir('./commands'):
      if commandfile.endswith('.py'):
         await bot.load_extension(f'commands.{commandfile[:-3]}')
   print('[BOT] All additional commands load!')

async def mainSetup():
   async with bot:
      await load_extensions()
      await bot.start(TOKEN)

asyncio.run(mainSetup())
