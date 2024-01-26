import os
import re
import json
import discord
import requests

from dataclasses import dataclass
from discord.ext import commands

@dataclass
class AudioSample:
   rawSource: str = None
   title: str = None
   author: str = None
   duration: str = None
   thumbnail: str = None
   audioSource: str = None

@dataclass
class PlaylistSample(AudioSample):
   playlist: list = None

class TimeHandler():
   def __init__(self) -> None:
      pass

   @classmethod
   def timeConverter(cls, time: int) -> str:
      if not isinstance(time, int): time = int(time)

      cls.seconds = time % 60
      cls.minutes = (time // 60) % 60
      cls.hours = time // 3600

      if cls.seconds < 10: cls.seconds = f'0{cls.seconds}'
      if cls.minutes < 10: cls.minutes = f'0{cls.minutes}'

      if cls.hours > 0:
         return f'{cls.hours}:{cls.minutes}:{cls.seconds}'
      else:
         return f'{cls.minutes}:{cls.seconds}'
   
   @classmethod
   def millisecondsConverter(cls, time: int) -> str:
      time = time//1000

      cls.seconds = time % 60
      cls.minutes = (time // 60) % 60
      cls.hours = time // 3600

      if cls.seconds < 10: cls.seconds = f'0{cls.seconds}'
      if cls.minutes < 10: cls.minutes = f'0{cls.minutes}'

      if cls.hours > 0:
         return f'{cls.hours}:{cls.minutes}:{cls.seconds}'
      else:
         return f'{cls.minutes}:{cls.seconds}'

class MessageHandler():
   @classmethod
   def embedMessage(cls, title: str = '', description: str = '', footer: str = '', thumbnail: str = '', placeTimestamp: bool = False):
      message = discord.Embed(title=title, description=description)
      message.set_footer(text=footer)
      message.set_thumbnail(url=thumbnail)
      return message

class BotConnect():
   @classmethod
   async def botConnect(cls, context: commands.Context, debuggable: bool = False) -> bool:
      match context.author.voice:
         case None:
            await context.channel.send(embed=MessageHandler.embedMessage(title='Connect to the voice channel!', description='I can\'t playing music for you!'))
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

class YoutubeUpdate():
   CIPHER_VERSION = (requests.get('https://www.youtube.com/iframe_api').text).split(';')[0].split('/')[5].replace('\\', '')
   FULL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'handlers', 'algorithmData.json')

   def __init__(self) -> None:
      self.checkUpdate()

   @classmethod
   def checkUpdate(cls) -> None:
      # print(cls.FULL_DIR)
      if os.path.exists(cls.FULL_DIR):
         with open(cls.FULL_DIR, mode='r', encoding='UTF-8') as file:
            jsonData = json.load(file)

      if not os.path.exists(cls.FULL_DIR):
         with open(cls.FULL_DIR, mode='w+', encoding='UTF-8') as file:
            try:
               jsonData = json.load(file)
            except json.decoder.JSONDecodeError:
               jsonData = {"version": 0}

      match jsonData['version'] != cls.CIPHER_VERSION:
         case True:
            functionParser = (requests.get(f'https://www.youtube.com/s/player/{cls.CIPHER_VERSION}/player_ias.vflset/en_US/base.js').text).replace('\n', '')
            mainFunction = re.search(r"[\{\d\w\(\)\\.\=\"]*?;(\S{1,5}\...\(.\,..?\)\;){3,}.*?}", functionParser)[0]
            subFunction = re.findall(r"var "+re.findall(r'(\w{2,})\...', mainFunction)[0]+r"={.+?};", functionParser)[0]

            jsonData['timestamp'] = re.findall(r'signatureTimestamp:\S{5}', functionParser)[-1].replace('signatureTimestamp:', '')
            jsonData['version'] = cls.CIPHER_VERSION
            jsonData['algorithm'] = f'{subFunction} {mainFunction};'
            jsonData['download_key'] = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'

            with open(cls.FULL_DIR, mode='w+') as file:
               json.dump(jsonData, file, ensure_ascii=False)
      print('[Utilite] Update complete...')
