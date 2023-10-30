from discord.ext import commands
from handlers.handler import MessageHandler

class Pause(commands.Cog):
   @commands.command(name='pause',aliases=['ps', 'PS'])
   async def pause(self, context: commands.Context):
      if not context.voice_client.is_paused():
         context.voice_client.pause()
         await context.channel.send(embed=MessageHandler.embedMessage('Paused', 'To continue listening using:  `*resume` or `*r`'))

async def setup(bot):
   await bot.add_cog(Pause())
