from discord.interactions import Interaction
from discord.ui import Select, View
from discord import Interaction, SelectOption

class AudioMenu(Select):
   def __init__(self, audioSourceList: list[dict[str, str, str]] = []) -> None:
      super().__init__(placeholder='\"Smart\" search music', options=[SelectOption(label=s['title'], value=i, description=s['author']) for i, s in enumerate(audioSourceList)])

   async def callback(self, interaction: Interaction) -> None:
      await interaction.response.send_message(content='')

class InteractiveView(View):
   def __init__(self, *, timeout: float | None = 180, uiItem = None) -> None:
      super().__init__(timeout=timeout)
      self.add_item(uiItem)

   async def interaction_check(self, interaction: Interaction) -> bool:
      self.stop()
      return await super().interaction_check(interaction)