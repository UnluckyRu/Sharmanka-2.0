import asyncio
import random

from discord.ext import commands
from discord import FFmpegPCMAudio

from handlers.serverQueue import Queue
from handlers.searchEngine import SearchManager
from handlers.handler import MessageHandler, BotConnect

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class MockObject(commands.Cog):
   def __init__(self) -> None:
      pass

   @classmethod
   async def connecting(cls, context: commands.Context, notification):
      if await BotConnect.botConnect(context=context):
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Bot connect...'))
         return

      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...'))

   @classmethod
   async def playAudio(cls, context: commands.Context, notification, audioSource: str):
      context.voice_client.play(FFmpegPCMAudio(source=audioSource, **FFMPEG_OPTIONS, executable='ffmpeg'))

      if not context.voice_client.is_playing():
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Playing audio...'))
         return
      
      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                        ':white_check_mark: Playing audio...'))

   @classmethod
   async def pause(cls, context: commands.Context, notification):
      context.voice_client.pause()
      if not context.voice_client.is_paused():
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Pause audio...'))
         return
      
      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                        ':white_check_mark: Playing audio...\n\n' + 
                                                                                        ':white_check_mark: Pause audio...\n\n'))

   @classmethod
   async def resume(cls, context: commands.Context, notification):
      context.voice_client.resume()
      if not context.voice_client.is_playing():
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Resume audio...'))
         return

      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                        ':white_check_mark: Playing audio...\n\n' + 
                                                                                        ':white_check_mark: Pause audio...\n\n' +
                                                                                        ':white_check_mark: Resume audio...\n\n' +
                                                                                        ':arrows_counterclockwise: Checking the platforms engine...\n\n'))

   @classmethod
   async def checkEngine(cls, context: commands.Context, notification, dataSet: list):  
      try:
         for _, source in enumerate(dataSet):
            queryType, audioObject = await SearchManager.findAudio(searchQuery=source[0], platform=source[1])

            match queryType:
               case 'linkSource':
                  if not (audioObject['title'] or audioObject['author'] or audioObject['thumbnail'] or audioObject['audioSource']): raise Exception()
               case 'textSource':
                  if not (audioObject['title'] or audioObject['author'] or audioObject['thumbnail'] or audioObject['audioSource']): raise Exception()
               case 'playlist':
                  if not isinstance(audioObject['playlist'], list) or not isinstance(audioObject['playlist'][0], dict): raise Exception()
               case 'liveSource':
                  if audioObject['duration'] != 'LIVE' and audioObject['audioSource'] is None: raise Exception()
               case 'bulkRequests':
                  if not isinstance(audioObject, list) or len(audioObject) != 10: raise Exception()
                  break
      except Exception:
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Platforms engine is broken...'))
         return
      else:
         await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                           ':white_check_mark: Playing audio...\n\n' + 
                                                                                           ':white_check_mark: Pause audio...\n\n' +
                                                                                           ':white_check_mark: Resume audio...\n\n' +
                                                                                           ':white_check_mark: Platforms engine working...\n\n'))  

   @classmethod
   async def queueUsing(cls, context: commands.Context, notification, audioSource: list):     
      if context.voice_client.is_playing():
         Queue.putQueue(context.guild.id, {'rawSource': 'Diagnostic test!',
                                             'title': 'Testing...',
                                             'author': 'Sharmanka 2.0',
                                             'duration': 'Uknown',
                                             'thumbnail': None,
                                             'audioSource': audioSource,})

      if len(Queue.returnQueue(context.guild.id)[1]) == 0:
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Adding in Queue...'))
         return
   
      context.voice_client.stop()
      context.voice_client.play(FFmpegPCMAudio(source=Queue.getQueue(context.guild.id), **FFMPEG_OPTIONS, executable='ffmpeg'))

      if not context.voice_client.is_playing():
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Getting from Queue...'))
         return

      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                        ':white_check_mark: Playing audio...\n\n' + 
                                                                                        ':white_check_mark: Pause audio...\n\n' +
                                                                                        ':white_check_mark: Resume audio...\n\n' +
                                                                                        ':white_check_mark: Platforms engine working...\n\n'
                                                                                        ':white_check_mark: Using Queue...\n\n'))

   @classmethod
   async def stop(cls, context: commands.Context, notification):
      context.voice_client.stop() 
      if context.voice_client.is_playing():
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Stop song playing...'))
         return

      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                        ':white_check_mark: Playing audio...\n\n' + 
                                                                                        ':white_check_mark: Pause audio...\n\n' +
                                                                                        ':white_check_mark: Resume audio...\n\n' +
                                                                                        ':white_check_mark: Platforms engine working...\n\n' +
                                                                                        ':white_check_mark: Using Queue...\n\n' +
                                                                                        ':white_check_mark: Stop playing...\n\n'))

   @classmethod
   async def leave(cls, context: commands.Context, notification):
      Queue.deleteQueue(context.guild.id)
      await context.voice_client.disconnect()
      if Queue.returnQueue(context.guild.id)[1]:
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Clear Queue...'))
         return

      if context.voice_client:
         await notification.edit(embed=MessageHandler.embedMessage('Check FAILED...', ':x: Leave from channel...'))
         return
      
      await notification.edit(embed=MessageHandler.embedMessage('Complex bot check...', ':white_check_mark: Bot connect...\n\n' + 
                                                                                        ':white_check_mark: Playing audio...\n\n' + 
                                                                                        ':white_check_mark: Pause audio...\n\n' +
                                                                                        ':white_check_mark: Resume audio...\n\n' +
                                                                                        ':white_check_mark: Platforms engine working...\n\n' +
                                                                                        ':white_check_mark: Using Queue...\n\n' +
                                                                                        ':white_check_mark: Stop playing...\n\n' +
                                                                                        ':white_check_mark: Leave channel...\n\n'))

   @commands.command(name='diagnostics', aliases=['ds'])
   async def complexTest(self, context: commands.Context):
      CheckDataset = [['Resonanse - HOME', 'p'],  ['https://www.youtube.com/watch?v=8GW6sLrK40k', ''], ['https://www.youtube.com/playlist?list=PL8bbQ8wOE8ty19XNQGWHQ2rk17RaQnyWq', ''], 
                      ['Resonanse - HOME', 'vp'], ['https://vk.com/audio193027317_456239562_2cc61733bbf812b7d7', ''], ['https://vk.com/music/playlist/300732341_22_34160a4377a1359a51', ''], 
                      ['Resonanse - HOME', 'yp'], ['https://music.yandex.ru/album/17743313/track/89055249', ''], ['https://music.yandex.ru/users/yamusic-bestsongs/playlists/19199281', ''],
                      ['Resonanse - HOME', 'sp'], ['https://music.yandex.ru/album/24679615', ''], ['Resonanse - HOME', 'bulkRequests']]
      
      Audiolink = "https://cs5-4v4.vkuseraudio.net/s/v1/acmp/AyyesKi97Df4cjq7cJoEvtlADaIcaHzGzTO2tr8HS7pCo1PiEG1s_4_94xFFJ464hpmS3d4jZnHbJA7IP6J1q4txe59F8izmot0X64XajJU9h_MYm-FCHMtuQpowxud3isZ4xYk1IBMFCt7sXDRypMjBMHBlSApPWSHHcSdiHUBafCWw8Q.mp3"

      notification = await context.send(embed=MessageHandler.embedMessage('Complex bot check...'))

      await self.connecting(context, notification)
      await asyncio.sleep(2)
      await self.playAudio(context, notification, Audiolink)
      await asyncio.sleep(2)
      await self.pause(context, notification)
      await asyncio.sleep(2)
      await self.resume(context, notification)
      await asyncio.sleep(2)
      await self.checkEngine(context, notification, CheckDataset)
      await asyncio.sleep(2)
      await self.queueUsing(context, notification, Audiolink)
      await asyncio.sleep(2)
      await self.stop(context, notification)
      await asyncio.sleep(2)
      await self.leave(context, notification)

      await notification.edit(embed=MessageHandler.embedMessage('Success', ':white_check_mark: Diagnostic complete successfully\n\n' +
                                                                           'Enjoy using my bot! -Developer'))

async def setup(bot):
   await bot.add_cog(MockObject())
