from discord.ext import commands
from handlers.serverQueue import Queue

class Leave(commands.Cog):
   @commands.command(name='leave', aliases=['lv', 'LV'])
   async def leave(self, context: commands.Context):
      if not context.voice_client: return
      Queue.deleteQueue(context.guild.id)
      await context.voice_client.disconnect()

async def setup(bot):
   await bot.add_cog(Leave())