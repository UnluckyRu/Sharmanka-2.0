import discord
from discord.ext import commands
from discord import FFmpegPCMAudio

from handlers.searchEngine import ExtractManager, SearchManager
from handlers.interaction import audioMenu, InteractiveView

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Player(commands.Cog):
   def __init__(self, bot) -> None:
      self.bot: commands.Bot = bot
      self.queueList = {}

   async def basicsConnect(self, context: commands.Context):
      match self.queueList.get(f'{context.guild.id}'):
         case None:
            if self.queueList:
               self.queueList.update({f'{context.guild.id}': []})
            else:
               self.queueList = {f'{context.guild.id}': []}

      match context.author.voice:
         case None:
            await context.channel.send(embed=embedPackage(title='Connect to the voice channel!', description='Else i can\'t playing music for you!'))
            return True
         case _:
            match context.voice_client:
               case None:
                  try: 
                     await context.author.voice.channel.connect()
                     return False
                  except: 
                     return False
               case _: 
                  return False

   @commands.command(name='play', aliases=['p'])
   async def play(self, context: commands.Context, *, searchRequest: str = '') -> None:
      if await self.basicsConnect(context): return

      notificationMessage = await context.send(embed=embedPackage('Searching tracks...', 'Please wait! \n It may take a couple minutes!'))
      try:
         self.audioObject = SearchManager(searchRequest).findAudio()
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'Something went wrong while searching for your track!'))
         return

      if context.voice_client.is_playing():
         self.queueList[f'{context.guild.id}'].append(self.audioObject)
         await notificationMessage.edit(embed=embedPackage("New song added in queue", 
                                                           f"Title: [{self.audioObject['title']}]({self.audioObject['rawSource']}) \n" +
                                                           f"Uploader: {self.audioObject['author']}\n\n" +
                                                           f"Duration: {self.audioObject['duration']}", 
                                                           thumbnail=self.audioObject['thumbnail']))
      else:
         await notificationMessage.edit(embed=embedPackage('Song added', 
                                                           f"Title: [{self.audioObject['title']}]({self.audioObject['rawSource']}) \n" +
                                                           f"Uploader: {self.audioObject['author']}\n\n" +
                                                           f"Duration: {self.audioObject['duration']}",
                                                           thumbnail=self.audioObject['thumbnail']))
         
         context.voice_client.play(FFmpegPCMAudio(source=self.audioObject['audioSource'], **FFMPEG_OPTIONS, executable='ffmpeg'), after=lambda x=None: self.queuePlay(context=context))

   @commands.command(name='searchPlay', aliases=['sp'])
   async def searchPlay(self, context: commands.Context, *, searchRequest: str = ''):
      if await self.basicsConnect(context): return 0

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
         self.externalAudioObject = ExtractManager().getFromSource(sourceQuery=self.audioSearchList[int(self.selectMenu.values[0])]['url'], queryType='linkSource')
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'When starting your track, something went wrong! \n Changing your search term may help.'), view=None)
         return

      self.queueList[f'{context.guild.id}'].append(self.externalAudioObject)

      if context.voice_client.is_playing():
         await notificationMessage.edit(embed=embedPackage("New song added in queue", 
                                                           f"Title: [{self.externalAudioObject['title']}]({self.audioSearchList[int(self.selectMenu.values[0])]['url']}) \n" +
                                                           f"Uploader: {self.externalAudioObject['author']}\n\n" +
                                                           f"Duration: {self.externalAudioObject['duration']}", 
                                                           thumbnail=self.externalAudioObject['thumbnail']))
      else:
         await notificationMessage.edit(embed=embedPackage('Song added', 
                                                           f"Title: [{self.externalAudioObject['title']}]({self.audioSearchList[int(self.selectMenu.values[0])]['url']}) \n" +
                                                           f"Uploader: {self.externalAudioObject['author']}\n\n" +
                                                           f"Duration: {self.externalAudioObject['duration']}",
                                                           thumbnail=self.externalAudioObject['thumbnail']))
         
         self.queuePlay(context=context)

   @commands.command(name='playlist', aliases=['pp'])
   async def playlistPlay(self, context: commands.Context, *, searchRequest: str = ''):
      if await self.basicsConnect(context): return
      
      notificationMessage = await context.send(embed=embedPackage('Downloading playlist...', 
                                                                  'Please wait! \n'
                                                                  'It may take a couple minutes! \n'
                                                                  '`Unavailable tracks will be skipped automatically!`'))
      try:
         self.externalAudioObject = SearchManager(searchRequest).findAudio()
      except:
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'Something went wrong while downloading for your playlist!'))
         return

      await notificationMessage.edit(embed=embedPackage('Adding song in queue...'))
      try:
         list(map(self.queueList[f'{context.guild.id}'].append, self.externalAudioObject['playlist']))
      except: 
         await notificationMessage.edit(embed=embedPackage('Sorry!', 'Something went wrong while insert songs into queue!'))
         return

      if context.voice_client.is_playing():
         await notificationMessage.edit(embed=embedPackage("New playlist songs added in queue",
                                                           f"Title: {self.externalAudioObject['title']}\n\n "
                                                           f"Amount: {len(self.externalAudioObject)}",  
                                                           thumbnail=self.externalAudioObject['thumbnail']))
      else:
         await notificationMessage.edit(embed=embedPackage('Playlist songs added', 
                                                           f"Title: {self.externalAudioObject['title']}\n\n "
                                                           f"Amount: {len(self.externalAudioObject)}",  
                                                           thumbnail=self.externalAudioObject['thumbnail']))
         self.queuePlay(context)

   @commands.command(name='queue', aliases=['q'])
   async def queue(self, context: commands.Context):
      if not self.queueList.get(f'{context.guild.id}'): 
         await context.channel.send(embed=embedPackage('Queue empty', 'You can play your audio using:  `*play(p) {song}` or `*sp {song}`'))
         return
      
      await context.channel.send(embed=embedPackage(f'{len(self.queueList[f"{context.guild.id}"])} songs in queue:', 
                                                   ''.join(str(index+1)+'.'+'`'+'['+queueListElement['duration']+']'+'` '+queueListElement['title']+'\n' for index, queueListElement in enumerate(self.queueList[f'{context.guild.id}']))))

   @commands.command(name='resume', aliases=['r'])
   async def resume(self, context: commands.Context):
      if not context.voice_client.is_playing():
         context.voice_client.resume()
         await context.channel.send(embed=embedPackage('Resumed', 'To pause listening using:  `*pause` or `*ps`'))

   @commands.command(name='pause',aliases=['ps'])
   async def pause(self, context: commands.Context):
      if not context.voice_client.is_paused():
         context.voice_client.pause()
         await context.channel.send(embed=embedPackage('Paused', 'To continue listening using:  `*resume` or `*r`'))

   @commands.command(name='stop', aliases=['s'])
   async def stop(self, context: commands.Context):
      context.voice_client.stop()
      self.queueList[f'{context.guild.id}'].clear()
      await context.channel.send(embed=embedPackage('Stopped', 'You can\'t recover queue.\nTo start listening using:  `*p(lay) {song}` or `*sp {song}`'))
      
   @commands.command(name='skip', aliases=['sk'])
   async def skip(self, context: commands.Context):
      context.voice_client.stop()
      await context.channel.send(embed=embedPackage('Skipped', 'Track was skiped.\nEnjoy listening to the next tracks!'))
      
   @commands.command(name='leave', aliases=['lv'])
   async def leave(self, context: commands.Context):
      if not context.voice_client: return
      await context.voice_client.disconnect()

   @commands.command(name='t')
   async def testNewComand(self, context: commands.Context):
      print(self.queueList)

   def queuePlay(self, context: commands.Context) -> None:
      if not self.queueList.get(f'{context.guild.id}'): return
      recievedAudioObject = self.queueList.get(f'{context.guild.id}').pop(0)
      context.voice_client.play(FFmpegPCMAudio(source=recievedAudioObject['audioSource'], **FFMPEG_OPTIONS, executable='ffmpeg'), after=lambda x=None: self.queuePlay(context))

def embedPackage(title: str = '', description: str = '', footer: str = '', thumbnail: str = '', placeTimestamp: bool = False):
   embedBlock = discord.Embed(title=title, description=description)
   embedBlock.set_footer(text=footer)
   embedBlock.set_thumbnail(url=thumbnail)
   return embedBlock

async def setup(bot):
   await bot.add_cog(Player(bot))