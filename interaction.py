from discord.ui import Select, View
from discord import Interaction, SelectOption

class DropMenu(Select):
   def __init__(self):
      super().__init__(placeholder='\"Smart\" search music', options=[SelectOption(label='123')], custom_id='MusicDropMenu')

   async def callback(self, interaction: Interaction):
      await interaction.response.send_message(self.values, view=None)