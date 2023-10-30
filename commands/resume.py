from discord.ext import commands
from handlers.handler import MessageHandler

class Resume(commands.Cog):
   @commands.command(name='resume', aliases=['r', 'R'])
   async def resume(self, context: commands.Context):
      if not context.voice_client.is_playing():
         context.voice_client.resume()
         await context.channel.send(embed=MessageHandler.embedMessage('Resumed', 'To pause listening using:  `*pause` or `*ps`'))

async def setup(bot):
   await bot.add_cog(Resume())
