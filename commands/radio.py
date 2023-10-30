import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from handlers.serverQueue import Queue
from handlers.searchEngine import SearchManager
from handlers.handler import MessageHandler, BotConnect

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Radio(commands.Cog):
   def __init__(self, bot) -> None:
      self.bot = bot

   async def songPlay(self, context: commands.Context):
      await context.voice_client.play(PCMVolumeTransformer(FFmpegPCMAudio(source=Queue.getQueue(context.guild.id), **FFMPEG_OPTIONS, executable='ffmpeg'), 0.5), 
                                      after=lambda e: asyncio.run_coroutine_threadsafe(self.songPlay(context), context.voice_client.loop))

   @commands.command(name='radio', aliases=['live'])
   async def radio(self, context: commands.Context, *, searchRequest: str = ''):
      if await BotConnect.botConnect(context): return

      notificationMessage = await context.send(embed=MessageHandler.embedMessage('Trying start live stream...', 'Please wait! \n It may take a couple minutes!'))
      try:
         _, audioObject = await SearchManager.findAudio(searchQuery=searchRequest, loop=self.bot.loop)
      except:
         await notificationMessage.edit(embed=MessageHandler.embedMessage('Sorry!', 'Something went wrong while start live!'))
         return
      
      Queue.putQueue(context.guild.id, audioObject)
      await notificationMessage.edit(embed=MessageHandler.embedMessage("Song added in queue", 
                                                         f"Title: [{audioObject['title']}]({audioObject['rawSource']}) \n" +
                                                         f"Uploader: {audioObject['author']}\n\n" +
                                                         f"Duration: {audioObject['duration']}", 
                                                         thumbnail=audioObject['thumbnail']))
      
      if not context.voice_client.is_playing() and not context.voice_client.is_paused():  
         await self.songPlay(context)

async def setup(bot):
   await bot.add_cog(Radio(bot))
