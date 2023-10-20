import asyncio

class LeaveControl():
   def __init__(self, context: object, voiceClient: object, embedPackage: object, timerToLeave: int):
      self.context = context
      self.voiceClient = voiceClient
      self.embedPackage = embedPackage
      self.timerToLeave = timerToLeave

   async def autoLeave(self):
      membersList = [source.id for index, source in enumerate(self.context.channel.members)]
      activeMembers = membersList.remove(1110944334162972732) or membersList

      if not bool(activeMembers):
         await self.context.send(embed=self.embedPackage('Channel leave', '**Disconnect from the channel** \n Reason: `Empty voice channel`'))
         return True

      if self.voiceClient.is_paused():
         if self.timerToLeave == 900:
            self.fogotNotification = await self.context.send(embed=self.embedPackage('Attention', '**Disconnect after remaning 15 minutes!**  \n Reason: `I\'m on pause!`'))
         if self.timerToLeave == 1800:
            await self.fogotNotification.edit(embed=self.embedPackage('Channel leave', '**Disconnect from the channel** \n Reason: `Too long stay in pause...`'))
            return True
         
      if not self.voiceClient.is_playing() and not self.voiceClient.is_paused() and self.timerToLeave == 600:
         await self.context.send(embed=self.embedPackage('Channel leave', '**Disconnect from the channel** \n Reason: `Long AFK`'))
         return True

      if not self.voiceClient.is_playing():
         self.timerToLeave += 1

      if self.voiceClient.is_playing():
         self.timerToLeave = 0
         
      await asyncio.sleep(1)
