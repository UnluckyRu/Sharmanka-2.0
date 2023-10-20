class Connecter():
   def __init__(self, context: object, queueList: dict, embedPackage: object) -> None:
      self.context = context
      self.queueList = queueList
      self.embedPackage = embedPackage

   async def queueCreator(self) -> dict:
      match self.queueList.get(f'{self.context.guild.id}'):
         case None:
            if self.queueList:
               self.queueList.update({f'{self.context.guild.id}': []})
            else:
               self.queueList = {f'{self.context.guild.id}': []}
      return self.queueList

   async def botConnect(self) -> bool:
      match self.context.author.voice:
         case None:
            await self.context.channel.send(embed=self.embedPackage(title='Connect to the voice channel!', description='I can\'t playing music for you!'))
            return True
         case _:
            match self.context.voice_client:
               case None:
                  try: 
                     await self.context.author.voice.channel.connect()
                     return False
                  except: 
                     return False
               case _: 
                  return False

   async def autoConnect(self) -> dict | None:
      if await self.botConnect(): return self.queueList
      return await self.queueCreator()
