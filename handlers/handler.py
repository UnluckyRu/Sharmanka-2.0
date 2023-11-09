import os
import re
import json
import discord
import requests

class TimeHandler():
   def __init__(self) -> None:
      pass

   def timeConverter(self, time: int) -> str:
      if not isinstance(time, int): time = int(time)

      self.seconds = time % 60
      self.minutes = (time // 60) % 60
      self.hours = time // 3600

      if self.seconds < 10: self.seconds = f'0{self.seconds}'
      if self.minutes < 10: self.minutes = f'0{self.minutes}'

      if self.hours > 0:
         return f'{self.hours}:{self.minutes}:{self.seconds}'
      else:
         return f'{self.minutes}:{self.seconds}'
      
   def millisecondsConverter(self, time: int) -> str:
      time = time//1000

      self.seconds = time % 60
      self.minutes = (time // 60) % 60
      self.hours = time // 3600

      if self.seconds < 10: self.seconds = f'0{self.seconds}'
      if self.minutes < 10: self.minutes = f'0{self.minutes}'

      if self.hours > 0:
         return f'{self.hours}:{self.minutes}:{self.seconds}'
      else:
         return f'{self.minutes}:{self.seconds}'

class MessageHandler():
   @classmethod
   def embedMessage(cls, title: str = '', description: str = '', footer: str = '', thumbnail: str = '', placeTimestamp: bool = False):
      message = discord.Embed(title=title, description=description)
      message.set_footer(text=footer)
      message.set_thumbnail(url=thumbnail)
      return message

class BotConnect():
   @classmethod
   async def botConnect(cls, context: object) -> bool:
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
      print('[Utilite] Check update...')
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
