from discord.ext import commands
from handlers.serverQueue import Queue
from handlers.handler import MessageHandler

class Stop(commands.Cog):
   @commands.command(name='stop', aliases=['s', 'S'])
   async def stop(self, context: commands.Context):
      context.voice_client.stop()
      Queue.deleteQueue(context.guild.id)
      await context.channel.send(embed=MessageHandler.embedMessage('Stopped', 'You can\'t recover queue.\nTo start listening using:  `*p(lay) {song}` or `*sp {song}`'))

async def setup(bot):
   await bot.add_cog(Stop())
