import random
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from handlers.searchEngine import SearchManager
from handlers.ytGrabber import YtGrabber
from handlers.interaction import audioMenu, InteractiveView
from handlers.connectHelper import Connecter
from handlers.autoLeave import LeaveControl

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Player(commands.Cog):
   def __init__(self, bot) -> None:
      self.bot: commands.Bot = bot
      self.queueList = {}
      self.flag = False
      self.leaveObject = None

   async def queuePlay(self, context: commands.Context) -> None:
      self.timerToLeave = 0
      if type(self.leaveObject) is not LeaveControl:
         self.leaveObject = LeaveControl(context, context.voice_client, embedPackage, self.timerToLeave)

      if not self.queueList.get(f'{context.guild.id}'): return
      self.recievedAudioObject = self.queueList.get(f'{context.guild.id}').pop(0)

      context.voice_client.play(PCMVolumeTransformer(FFmpegPCMAudio(source=self.recievedAudioObject['audioSource'], **FFMPEG_OPTIONS, executable='ffmpeg'), 0.5),
                              after=lambda x=None: asyncio.run_coroutine_threadsafe(self.queuePlay(context), context.voice_client.loop))

      if not self.flag:
         self.flag = True
         while context.voice_client:         
            if await self.leaveObject.autoLeave():
               del self.queueList[f'{context.guild.id}']
               await context.voice_client.disconnect()
               self.flag = False
               self.leaveObject = None
               return

   @commands.command(name='play', aliases=['p', 'vp', 'yp', 'P', 'VP', 'YP'])
   async def play(self, context: commands.Context, *, searchRequest: str = '') -> None:
      self.context = context
      self.platform = context.message.content.split(' ')[0].replace('-', '')

      self.queueList = await Connecter(context, self.queueList, embedPackage).autoConnect()
      if f'{context.guild.id}' not in self.queueList: return

      notificationMessage = await context.send(embed=embedPackage('Searching for your request...', 'Please wait! \n It may take a couple minutes!'))
      try:
         self.queryType, self.audioObject = await SearchManager().findAudio(searchQuery=searchRequest, platform=self.platform)
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'Something went wrong while searching from your query!'))
         return

      match self.queryType:
         case 'playlist':
            self.queueList[f'{context.guild.id}'].extend(self.audioObject['playlist'])
            await notificationMessage.edit(embed=embedPackage("Playlist songs added in queue",
                                                              f"Title: [{self.audioObject['title']}]({self.audioObject['rawSource']})\n\n "
                                                              f"Amount: **{len(self.audioObject['playlist'])}**",  
                                                              thumbnail=self.audioObject['thumbnail']))
            
         case 'linkSource' | 'textSource':
            self.queueList[f'{context.guild.id}'].append(self.audioObject)
            await notificationMessage.edit(embed=embedPackage("Song added in queue", 
                                                              f"Title: [{self.audioObject['title']}]({self.audioObject['rawSource']}) \n" +
                                                              f"Uploader: {self.audioObject['author']}\n\n" +
                                                              f"Duration: {self.audioObject['duration']}", 
                                                              thumbnail=self.audioObject['thumbnail']))

      context = self.context
      if not context.voice_client.is_playing() and not context.voice_client.is_paused():
         await self.queuePlay(context=context)

   @commands.command(name='radio', aliases=['live'])
   async def radio(self, context: commands.Context, *, searchRequest: str = ''):
      self.queueList = await Connecter(context, self.queueList, embedPackage).autoConnect()
      if f'{context.guild.id}' not in self.queueList: return

      notificationMessage = await context.send(embed=embedPackage('Trying start live stream...', 'Please wait! \n It may take a couple minutes!'))
      try:
         self.queryType, self.audioObject = await SearchManager().findAudio(searchQuery=searchRequest, loop=self.bot.loop)
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'Something went wrong while start live!'))
         return
      
      self.queueList[f'{context.guild.id}'].append(self.audioObject)
      await notificationMessage.edit(embed=embedPackage("Song added in queue", 
                                                        f"Title: [{self.audioObject['title']}]({self.audioObject['rawSource']}) \n" +
                                                        f"Uploader: {self.audioObject['author']}\n\n" +
                                                        f"Duration: {self.audioObject['duration']}", 
                                                        thumbnail=self.audioObject['thumbnail']))
      
      if not context.voice_client.is_playing() and not context.voice_client.is_paused():  
         await self.queuePlay(context=context)

   @commands.command(name='searchPlay', aliases=['sp', 'SP'])
   async def searchPlay(self, context: commands.Context, *, searchRequest: str = ''):
      self.queueList = await Connecter(context, self.queueList, embedPackage).autoConnect()
      if f'{context.guild.id}' not in self.queueList: return

      notificationMessage = await context.send(embed=embedPackage('Searching tracks...', 'Please wait! \n It may take a couple minutes!'))
      try:
         self.audioSearchList = await SearchManager(searchRequest).audioList()
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'Something went wrong while searching for your track!'), view=None)
         return

      self.selectMenu = audioMenu(audioSourceList=self.audioSearchList)
      self.interactionView = InteractiveView(uiItem=self.selectMenu)
      self.interactionView.notificationMessage = await notificationMessage.edit(embed=embedPackage('Select soundtrack:'), view=self.interactionView)
      await self.interactionView.wait()

      await notificationMessage.edit(embed=embedPackage('Starting track...'), view=None)
      try:
         _, self.externalAudioObject = await YtGrabber().getFromSource(sourceQuery=self.audioSearchList[int(self.selectMenu.values[0])]['url'], queryType='linkSource')
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'When starting your track, something went wrong! \n Changing your search term may help.'), view=None)
         return

      self.queueList[f'{context.guild.id}'].append(self.externalAudioObject)
      await notificationMessage.edit(embed=embedPackage("Song added in queue", 
                                                        f"Title: [{self.externalAudioObject['title']}]({self.externalAudioObject['rawSource']}) \n" +
                                                        f"Uploader: {self.externalAudioObject['author']}\n\n" +
                                                        f"Duration: {self.externalAudioObject['duration']}",
                                                        thumbnail=self.externalAudioObject['thumbnail']))

      if not context.voice_client.is_playing():
         await self.queuePlay(context=context)

   @commands.command(name='queue', aliases=['q', 'Q'])
   async def queue(self, context: commands.Context, *, pageNumber: int = 1):
      if not self.queueList.get(f'{context.guild.id}') and not context.voice_client.is_playing():
         await context.channel.send(embed=embedPackage('Queue empty', 'You can play your audio using:  `*play(p) {song}` or `*sp {song}`'))
         return

      self.indexShift = 20*(pageNumber-1)
      self.maxPages = (len(self.queueList[f'{context.guild.id}']) // 20) + 1

      if pageNumber < 0: self.currentPage = 1
      if pageNumber > len(self.queueList[f'{context.guild.id}']): self.currentPage = self.maxPages
      self.currentPage = pageNumber

      self.pageList = "".join(f"{(index+1)+self.indexShift}. `[{queueListElement['duration']}]` {queueListElement['title']}\n" for index, queueListElement in enumerate(self.queueList[f'{context.guild.id}'][20*(pageNumber-1):(20*(pageNumber-1))+20:]))

      await context.channel.send(embed=embedPackage('**Now playing:**\n' +
                                                    f"```[{self.recievedAudioObject['duration']}] {self.recievedAudioObject['title']}``` \n\n" + 
                                                    f"{'**Songs in queue:**' if len(self.queueList[f'{context.guild.id}']) != 0 else '**Songs queue is empty!**'} \n\n",
                                                    self.pageList,
                                                    f"Pages: {self.currentPage} / {self.maxPages}" if len(self.queueList[f'{context.guild.id}']) != 0 else ''))
   
   @commands.command(name='shuffle', aliases=['sh', 'SH'])
   async def shuffleContent(self, context: commands.Context, *, amountShuffle: int = 1):
      if not self.queueList.get(f'{context.guild.id}'): return
      for i in range(amountShuffle):
         random.shuffle(self.queueList.get(f'{context.guild.id}'))
      await context.channel.send(embed=embedPackage('Shuffled!', 'The contents in the queue are mixed forever!'))

   @commands.command(name='resume', aliases=['r', 'R'])
   async def resume(self, context: commands.Context):
      if not context.voice_client.is_playing():
         context.voice_client.resume()
         await context.channel.send(embed=embedPackage('Resumed', 'To pause listening using:  `*pause` or `*ps`'))

   @commands.command(name='pause',aliases=['ps', 'PS'])
   async def pause(self, context: commands.Context):
      if not context.voice_client.is_paused():
         context.voice_client.pause()
         await context.channel.send(embed=embedPackage('Paused', 'To continue listening using:  `*resume` or `*r`'))

   @commands.command(name='stop', aliases=['s', 'S'])
   async def stop(self, context: commands.Context):
      context.voice_client.stop()
      self.queueList[f'{context.guild.id}'].clear()
      await context.channel.send(embed=embedPackage('Stopped', 'You can\'t recover queue.\nTo start listening using:  `*p(lay) {song}` or `*sp {song}`'))
      
   @commands.command(name='skip', aliases=['sk', 'SK'])
   async def skip(self, context: commands.Context):
      context.voice_client.stop()
      await context.channel.send(embed=embedPackage('Skipped', f'Track was skiped.\nEnjoy listening to the next tracks!'))
      
   @commands.command(name='leave', aliases=['lv', 'LV'])
   async def leave(self, context: commands.Context):
      if not context.voice_client: return
      self.leaveObject = None
      self.flag = False
      del self.queueList[f'{context.guild.id}']
      await context.voice_client.disconnect()

   @commands.command(name='botHelp', aliases=['h'])
   async def helpCommand(self, context: commands.Context):
      await context.channel.send(embed = embedPackage('List of commands:', 
                                                      '`*p` - play song from YT (link, text, playlist, live)\n'
                                                      '`*vp` - play song from VK (link, text, playlist)\n'
                                                      '`*yp` - play song from Yandex Music (link, text, playlist, album)\n'
                                                      '`*sp` - seacrh and play song from title \n'
                                                      '`*sh` - shuffle the content in queue \n'
                                                      '`*q` - watch what audio is playing and other in queue \n'
                                                      '`*sk` - skip the now playing song \n'
                                                      '`*r` - resume playing song after the pause \n'
                                                      '`*s` - stop the playing music and clear queue \n'
                                                      '`*lv` - leave the channel and clear the queue'))

   @commands.command(name='t')
   async def testNewComand(self, context: commands.Context, *, searchRequest: str = ''):
      self.queueList = await Connecter(context, self.queueList, embedPackage).autoConnect()
      #self.queryType, self.audioObject = await SearchManager(searchRequest).findAudio()
      import requests
      import yt_dlp
      
      #print(self.audioObject['audioSource'].read())
      def streamLive(xy):
         x = requests.post('https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8', json={"videoId": "4xDzrJKXOOY", "context": {"client": {"clientName": "WEB", "clientVersion": "2.20231020.00.01"}}}).json()
         streamUrl = x['streamingData']['hlsManifestUrl']
         return streamUrl
      
      self.loop = self.bot.loop or asyncio.get_event_loop()
      x = await self.loop.run_in_executor(None, lambda: streamLive('123'))
      print(x)
      context.voice_client.play(FFmpegPCMAudio(source=x, **FFMPEG_OPTIONS, executable='ffmpeg'))

def embedPackage(title: str = '', description: str = '', footer: str = '', thumbnail: str = '', placeTimestamp: bool = False):
   embedBlock = discord.Embed(title=title, description=description)
   embedBlock.set_footer(text=footer)
   embedBlock.set_thumbnail(url=thumbnail)
   return embedBlock

async def setup(bot):
   await bot.add_cog(Player(bot))