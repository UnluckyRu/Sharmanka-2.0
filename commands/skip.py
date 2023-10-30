from discord.ext import commands
from handlers.handler import MessageHandler

class Skip(commands.Cog):
   @commands.command(name='skip', aliases=['sk', 'SK'])
   async def skip(self, context: commands.Context):
      context.voice_client.stop()
      await context.channel.send(embed=MessageHandler.embedMessage('Skipped', f'Track was skiped.\nEnjoy listening to the next tracks!'))

async def setup(bot):
   await bot.add_cog(Skip())