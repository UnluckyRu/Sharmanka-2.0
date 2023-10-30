import asyncio
from handlers.handler import MessageHandler

class LeaveControl():
   exitTime = 0
   classCounter = 0
   leaveTimes = {
      'warningLine': 900, 
      'pauseLine': 1800,
      'AFKLine': 600,      
   }

   @classmethod
   def addCounter(cls):
      cls.classCounter += 1
      return cls.classCounter

   @classmethod
   async def autoLeave(cls, context: object = None):
      if context is None: return

      membersList = [source.id for _, source in enumerate(context.channel.members)]
      activeMembers = membersList.remove(1110944334162972732) or membersList

      if not context.voice_client.is_playing():
         cls.exitTime += 1
         print(f"Time: {cls.exitTime}; CLSCounter: {cls.classCounter};")

      if context.voice_client.is_playing():
         cls.exitTime = 0

      if context.voice_client.is_paused():
         if cls.exitTime == cls.leaveTimes['warningLine']:
            cls.fogotNotification = await context.send(embed=MessageHandler.embedMessage('Attention', '**Disconnect after remaning 15 minutes!**  \n Reason: `I\'m on pause!`'))
         if cls.exitTime == cls.leaveTimes['pauseLine']:
            await cls.fogotNotification.edit(embed=MessageHandler.embedMessage('Channel leave', '**Disconnect from the channel** \n Reason: `Too long stay in pause...`'))
            await context.voice_client.disconnect()
            cls.classCounter = 0
            return
            
      if not bool(activeMembers):
         await context.send(embed=MessageHandler.embedMessage('Channel leave', '**Disconnect from the channel** \n Reason: `Empty voice channel`'))
         await context.voice_client.disconnect()
         cls.classCounter = 0
         return

      if not context.voice_client.is_playing() and not context.voice_client.is_paused() and cls.exitTime == cls.leaveTimes['AFKLine']:
         await context.send(embed=MessageHandler.embedMessage('Channel leave', '**Disconnect from the channel** \n Reason: `Long AFK`'))
         await context.voice_client.disconnect()
         cls.classCounter = 0
         return
         
      await asyncio.sleep(1)
