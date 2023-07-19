import discord
from discord.ext import commands
from discord.ui import Select, View

from discord import FFmpegPCMAudio, SelectOption

from searchEngine import SearchEngine
from interaction import DropMenu

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Player(commands.Cog):
   def __init__(self, bot) -> None:
      self.bot: commands.Bot = bot
      self.queueList = []

   async def basicsConnect(self, context: commands.Context):
      if context.author.voice is None:
         return await context.channel.send(embed=embedPackage(title='Connect to the voice channel!', description='Else i can\'t playing music for you!'))
      elif context.voice_client is None:
         try:
            await context.author.voice.channel.connect()
            return print('[BOT] All condition complete now!')
         except:
            print('[BOT] I can\'t connect to the voice channel!')
      else: print('[BOT] All condition complete already!')

   @commands.hybrid_command(name='play', with_app_command=True, aliases=['p'])
   async def play(self, context: commands.Context, *, searchRequest: str = '') -> None:
      await self.basicsConnect(context=context)

      try: 
         self.audioObject = SearchEngine().audioExtract(typeSearch='play', baseRequest=searchRequest)
         print(self.audioObject)
         #print('Audio source: ', audioLink, '\n', 'Videos ID: ', idList)
      except:
         print(f'Error! {searchRequest}')

      if context.voice_client.is_playing():
         self.queueList.append(self.audioObject)
         await context.channel.send(embed=embedPackage("New song added in queue", 
                                                      f"Title: {self.audioObject['title']} \n\n Duration: {self.audioObject['duration']}",
                                                      thumbnail=self.audioObject['thumbnail']))
         #print(queueList)
      else:
         await context.channel.send(embed=embedPackage('Song added', 
                                                      f"Title: {self.audioObject['title']} \n\n"+
                                                      f"Duration: {self.audioObject['duration']}",
                                                      thumbnail=self.audioObject['thumbnail']))
         
         context.voice_client.play(FFmpegPCMAudio(source=self.audioObject['audioLink'], **FFMPEG_OPTIONS, executable='ffmpeg'), after=lambda x=None: self.queuePlay(context=context))

   @commands.command(name='queue', aliases=['q'])
   async def queue(self, context: commands.Context):
      if not self.queueList: 
         await context.channel.send(embed=embedPackage('Queue empty', 'You can play your audio using:  `*play {song}` or `*p {song}`'))
         return 0
      
      await context.channel.send(embed=embedPackage(f'{len(self.queueList)} songs in queue:', 
                                                   ''.join(str(index+1)+'.'+'`'+'['+queueListElement['duration']+']'+'` '+queueListElement['title']+'\n' for index, queueListElement in enumerate(self.queueList))))

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
      self.queueList.clear()
      await context.channel.send(embed=embedPackage('Stoped', 'You can\'t recover queue.\nTo start listening using:  `*play {song}` or `*p {song}`'))

   @commands.command(name='leave', aliases=['lv'])
   async def leave(self, context: commands.Context):
      if not context.voice_client: return
      await context.voice_client.disconnect()

   @commands.command(name='searchPlay', aliases=['sp'])
   async def searchPlay(self, context: commands.Context, *, searchRequest: str = ''):
      await self.basicsConnect(context=context)

      try:
         audioObjectsList = SearchEngine().audioExtract(typeSearch='search', baseRequest=searchRequest)
      except:
         pass

      print(audioObjectsList)

   @commands.command(name='t')
   async def testNewComand(self, context: commands.Context):
      #self.audioObjectsList = SearchEngine().audioExtract(typeSearch='search', baseRequest='HOME - Resonance')

      self.dropMenu = DropMenu()

      self.interactionView = View()
      self.interactionView.add_item(self.dropMenu)

      await context.channel.send('Select music:', view=self.interactionView)

      await self.interactionView.wait()
      print(self.interactionView.values)

   def queuePlay(self, context) -> None:
      if not self.queueList: return
      recievedAudioObject = self.queueList.pop(0)
      context.voice_client.play(FFmpegPCMAudio(source=recievedAudioObject['audioLink'], **FFMPEG_OPTIONS, executable='ffmpeg'), after=lambda x=None: self.queuePlay(context))

def embedPackage(title: str = '', description: str = '', footer: str = '', thumbnail: str = '', placeTimestamp: bool = False):
   embedBlock = discord.Embed(title=title, description=description)
   embedBlock.set_footer(text=footer)
   embedBlock.set_thumbnail(url=thumbnail)
   return embedBlock

async def setup(bot):
   await bot.add_cog(Player(bot))