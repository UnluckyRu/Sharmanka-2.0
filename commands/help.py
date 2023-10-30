from discord.ext import commands
from handlers.handler import MessageHandler

class Help(commands.Cog):
   @commands.command(name='botHelp', aliases=['h'])
   async def helpCommand(self, context: commands.Context):
      await context.channel.send(embed = MessageHandler.embedMessage('List of commands:', 
                                                                     '`*p` - play song from YT (link, text, playlist, live)\n'
                                                                     '`*vp` - play song from VK (link, text, playlist)\n'
                                                                     '`*yp` - play song from Yandex Music (link, text, playlist, album)\n'
                                                                     '`*sp` - seacrh and play song from title \n'
                                                                     '`*sh` - shuffle the content in queue \n'
                                                                     '`*q` - watch what audio is playing and other in queue \n'
                                                                     '`*sk` - skip the now playing song \n'
                                                                     '`*r` - resume playing song after the pause \n'
                                                                     '`*s` - stop the playing music and clear queue \n'
                                                                     '`*lv` - leave the channel and clear the queue'))
   
async def setup(bot):
   await bot.add_cog(Help())