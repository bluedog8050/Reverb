import discord
from discord.ext import commands

with open('bot.key') as k:
    token = k.read()

bot = commands.Bot('!')#, pm_help = True)

# this specifies what extensions to load when the bot starts up
startup_extensions = ['cogs.reverb', 'cogs.extensions', 'cogs.debug', 'cogs.turntracker']

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

if __name__ == '__main__':
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

bot.run(token)