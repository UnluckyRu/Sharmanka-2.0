from discord.ext import commands
from handlers.serverQueue import Queue
from handlers.handler import MessageHandler

class GuildQueue(commands.Cog, Queue):
   @commands.command(name='queue', aliases=['q', 'Q'])
   async def showQueue(self, context: commands.Context, *, pageNumber: int = None):
      if pageNumber is None: pageNumber = 1
      
      recievedAudioObject, queueList = Queue.returnQueue(context.guild.id)
      
      if not queueList and not context.voice_client.is_playing():
         await context.channel.send(embed=MessageHandler().embedMessage('Queue empty', 'You can play your audio using:  `*play(p) {song}` or `*sp {song}`'))
         return
      
      indexShift = 20*(pageNumber-1)
      maxPages = (len(queueList) // 20) + 1

      if pageNumber < 0: currentPage = 1
      if pageNumber > len(queueList): currentPage = maxPages
      currentPage = pageNumber

      pageList = "".join(f"{(index+1)+indexShift}. `[{queueListElement['duration']}]` {queueListElement['title']}\n" for index, queueListElement in enumerate(queueList[20*(pageNumber-1):(20*(pageNumber-1))+20:]))

      await context.channel.send(embed=MessageHandler.embedMessage(title = "**Now playing:**\n" + 
                                                                         f"```[{recievedAudioObject['duration']}] {recievedAudioObject['title']}``` \n\n" + 
                                                                         f"{'**Songs in queue:**' if len(queueList) != 0 else '**Songs queue is empty!**'} \n\n", 
                                                                   description = pageList, 
                                                                   footer = f"Pages: {currentPage} / {maxPages}" if len(queueList) != 0 else ''))
   
async def setup(bot):
   await bot.add_cog(GuildQueue())