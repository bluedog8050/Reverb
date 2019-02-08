import discord
from discord.ext import commands

with open('bot.key') as k:
    token = k.read()

bot = commands.Bot('!')#, pm_help = True)

# this specifies what extensions to load when the bot starts up (found in cogs folder)
startup_extensions = ['reverb', 'turntracker', 'debug']

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
@commands.has_permissions(administrator = True)
async def load(ctx, extension_name : str):
    '''Loads an extension.'''
    try:
        bot.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))
        return
    await ctx.send('{} loaded.'.format(extension_name))

@bot.command()
@commands.has_permissions(administrator = True)
async def unload(ctx, extension_name : str):
    '''Unloads an extension.'''
    bot.unload_extension(extension_name)
    await ctx.send('{} unloaded.'.format(extension_name))

@bot.command()
@commands.has_permissions(administrator = True)
async def reload(ctx, extension_name : str):
    '''Reloads an extension.'''
    bot.unload_extension(extension_name)
    await ctx.send('{} unloaded.'.format(extension_name))
    try:
        bot.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))
        return
    await ctx.send('{} loaded.'.format(extension_name))

if __name__ == '__main__':
    for extension in startup_extensions:
        try:
            bot.load_extension('cogs.' + extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

bot.run(token)