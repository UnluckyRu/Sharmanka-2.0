class Queue():
   queueList = {}
   receivedSong = None

   def createQueue(self, guildID: str = None) -> dict:
      match self.queueList.get(f'{guildID}'):
         case None:
            if self.queueList:
               self.queueList.update({f'{guildID}': []})
            else:
               self.queueList = {f'{guildID}': []}

   @classmethod
   def putQueue(cls, guildID: str = None, songData: dict = None):
      cls.createQueue(cls, guildID)
      if not isinstance(songData, list):
         cls.queueList[f'{guildID}'].append(songData)
      if isinstance(songData, list):
         cls.queueList[f'{guildID}'].extend(songData)

   @classmethod
   def getQueue(cls, guildID: str = None):
      cls.receivedSong = cls.queueList.get(f'{guildID}').pop(0)
      return cls.receivedSong['audioSource']

   @classmethod
   def deleteQueue(cls, guildID: str = None):
      del cls.queueList[f'{guildID}']

   @classmethod
   def returnQueue(cls, guildID: str = None):
      return [cls.receivedSong, cls.queueList.get(f'{guildID}')]
   
   @classmethod
   def replaceQueue(cls, guildID: str = None, newQueue: list = None):
      if not isinstance(newQueue, list): return
      cls.queueList[f'{guildID}'] = newQueue
