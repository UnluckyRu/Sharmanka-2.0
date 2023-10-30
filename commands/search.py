import asyncio

from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from handlers.serverQueue import Queue
from handlers.ytGrabber import YtGrabber
from handlers.interaction import AudioMenu, InteractiveView
from handlers.searchEngine import SearchManager
from handlers.handler import MessageHandler, BotConnect

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Search(commands.Cog):
   async def songPlay(self, context: commands.Context):
      await context.voice_client.play(PCMVolumeTransformer(FFmpegPCMAudio(source=Queue.getQueue(context.guild.id), **FFMPEG_OPTIONS, executable='ffmpeg'), 0.5), 
                                      after=lambda e: asyncio.run_coroutine_threadsafe(self.songPlay(context), context.voice_client.loop))

   @commands.command(name='searchPlay', aliases=['sp', 'SP'])
   async def searchPlay(self, context: commands.Context, *, searchRequest: str = ''):
      self.platform = context.message.content.split(' ')[0].replace('-', '')
      if await BotConnect.botConnect(context): return

      notificationMessage = await context.send(embed=MessageHandler.embedMessage('Searching tracks...', 'Please wait! \n It may take a couple minutes!'))
      try:
         _, self.audioSearchList = await SearchManager().findAudio(searchQuery=searchRequest, platform=self.platform)
      except:
         await notificationMessage.edit(embed=MessageHandler.embedMessage('Sorry!', 'Something went wrong while searching for your track!'), view=None)
         return

      self.selectMenu = AudioMenu(audioSourceList=self.audioSearchList)
      self.interactionView = InteractiveView(uiItem=self.selectMenu)
      self.interactionView.notificationMessage = await notificationMessage.edit(embed=MessageHandler.embedMessage('Select soundtrack:'), view=self.interactionView)
      await self.interactionView.wait()

      await notificationMessage.edit(embed=MessageHandler.embedMessage('Starting track...'), view=None)
      try:
         _, self.externalAudioObject = await YtGrabber().getFromYoutube(sourceQuery=self.audioSearchList[int(self.selectMenu.values[0])]['url'], queryType='linkSource')
      except:
         await notificationMessage.edit(embed=MessageHandler.embedMessage('Sorry!', 'When starting your track, something went wrong! \n Changing your search term may help.'), view=None)
         return

      Queue.putQueue(context.guild.id, self.externalAudioObject)
      await notificationMessage.edit(embed=MessageHandler.embedMessage("Song added in queue", 
                                                                       f"Title: [{self.externalAudioObject['title']}]({self.externalAudioObject['rawSource']}) \n" +
                                                                       f"Uploader: {self.externalAudioObject['author']}\n\n" +
                                                                       f"Duration: {self.externalAudioObject['duration']}",
                                                                       thumbnail=self.externalAudioObject['thumbnail']))

      if not context.voice_client.is_playing() and not context.voice_client.is_paused():
         await self.songPlay(context)

async def setup(bot):
   await bot.add_cog(Search())
