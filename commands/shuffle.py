import random
from discord.ext import commands

from handlers.serverQueue import Queue
from handlers.handler import MessageHandler

class Shuffle(commands.Cog):
   @commands.command(name='shuffle', aliases=['sh', 'SH'])
   async def shuffleContent(self, context: commands.Context, *, amountShuffle: int = 1):
      _, self.queueList = Queue.returnQueue(context.guild.id)
      if not self.queueList: return
      for _ in range(amountShuffle):
         self.mixedQueue = random.shuffle(self.queueList)
      await context.channel.send(embed=MessageHandler.embedMessage('Shuffled!', 'The contents in the queue are mixed forever!'))
      Queue.replaceQueue(context.guild.id, list(self.mixedQueue))

async def setup(bot):
   await bot.add_cog(Shuffle())