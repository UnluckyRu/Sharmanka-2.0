import discord

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
