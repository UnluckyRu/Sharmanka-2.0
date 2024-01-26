import os
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from handlers.autoLeave import LeaveControl
from handlers.searchEngine import SearchManager
from handlers.serverQueue import Queue
from handlers.handler import MessageHandler, BotConnect

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

PREFIX = os.environ.get("PREFIX")
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Play(commands.Cog):
   async def songPlay(self, context: commands.Context):
      context.voice_client.play(PCMVolumeTransformer(FFmpegPCMAudio(source=Queue.getQueue(context.guild.id), **FFMPEG_OPTIONS, executable='ffmpeg'), 0.5), 
                                after=lambda e: asyncio.run_coroutine_threadsafe(self.songPlay(context), context.voice_client.loop))

   @commands.command(name='play', aliases=['p', 'vp', 'yp', 'P', 'VP', 'YP'])
   async def play(self, context: commands.Context, *, searchRequest: str = '') -> None:
      self.platform = context.message.content.split(' ')[0].replace(PREFIX, '')
      
      if await BotConnect.botConnect(context): return

      notificationMessage = await context.send(embed=MessageHandler.embedMessage('Searching for your request...', 'Please wait! \n It may take a couple minutes!'))
      try:
         queryType, audioObject = await SearchManager.findAudio(searchQuery=searchRequest, platform=self.platform)
      except:
         await notificationMessage.edit(embed=MessageHandler.embedMessage('Sorry!', 'Something went wrong while searching from your query!'))
         return

      match queryType:
         case 'playlist':
            Queue.putQueue(context.guild.id, audioObject.playlist)
            await notificationMessage.edit(embed=MessageHandler.embedMessage("Playlist songs added in queue",
                                                               f"Title: [{audioObject.title}]({audioObject.rawSource})\n\n "
                                                               f"Amount: **{len(audioObject.playlist)}**",  
                                                               thumbnail=audioObject.thumbnail))
            
         case 'linkSource' | 'textSource':
            Queue.putQueue(context.guild.id, audioObject)
            await notificationMessage.edit(embed=MessageHandler.embedMessage("Song added in queue", 
                                                               f"Title: [{audioObject.title}]({audioObject.rawSource}) \n" +
                                                               f"Uploader: {audioObject.author}\n\n" +
                                                               f"Duration: {audioObject.duration}", 
                                                               thumbnail=audioObject.thumbnail))
      
      if not context.voice_client.is_playing() and not context.voice_client.is_paused():
         await self.songPlay(context)
         
async def setup(bot: commands.Bot):
   await bot.add_cog(Play())