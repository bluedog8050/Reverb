import discord
from discord.ext import commands
import logging
import os
import sys
import datetime

#Print Copyright disclaimer
print('''Reverb Bot  Copyright © 2018  Derek Peterson
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; see LICENSE file for more information.''')

try:
    with open('bot.key') as k:
        token = k.read()
except FileNotFoundError as e:
    print('bot.key file not found!')
    print('Exiting program...')
    exit(0)

start_time = datetime.datetime.now()

bot = commands.Bot('!')

root = logging.getLogger('bot')
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
filter = logging.Filter('bot')
handler.addFilter(filter)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

try:
    import uptime as uptime_module
except:
    root.warn('Uptime module is not installed. use "pip3 install uptime" to resolve this warning')

print(f'Starting in {os.getcwd()}')

# this specifies what extensions to load when the bot starts up (found in cogs folder)
extensions_list = os.listdir(os.path.abspath('./cogs/'))
startup_extensions =[]
for x in extensions_list:
    if x.endswith('.py') and not x.startswith('__'):
        startup_extensions.append(x[:-3])
print(f'Loading startup cogs: {startup_extensions}')
#startup_extensions = ['reverb', 'turntracker', 'gamecommands', 'debug']

@bot.event
async def on_ready():
    root.info(f'Logged in as {bot.user.name} {bot.user.id}')

@bot.command()
@commands.has_permissions(administrator = True)
async def uptime(ctx):
    '''Yields system and bot uptime'''
    bot_time_delta = datetime.datetime.now() - start_time
    botuptime = '{0} Days, {1} Hours, {2} Minutes, and {3} Seconds'.format(str(bot_time_delta.days), str(bot_time_delta.seconds//3600), str((bot_time_delta.seconds//60)%60), str(bot_time_delta.seconds%60))
    sysuptime_seconds = sysuptime_seconds = int(uptime_module.uptime())
    sysuptime_delta = datetime.timedelta(seconds = sysuptime_seconds)
    sysuptime = '{0} Days, {1} Hours, {2} Minutes, and {3} Seconds'.format(str(sysuptime_delta.days), str(sysuptime_delta.seconds//3600), str((sysuptime_delta.seconds//60)%60), str(sysuptime_delta.seconds%60))
    await ctx.send(f'Reverb has been running for {botuptime}\nOS has been running for {sysuptime}')

@bot.command()
@commands.has_permissions(administrator = True)
async def restart(ctx):
    '''Admin Only. Restart Reverb bot.'''
    await ctx.send(f'Restarting bot...')
    exit(2)

@bot.command()
@commands.has_permissions(administrator = True)
async def load(ctx, extension_name : str):
    '''Admin Only. Loads an extension.'''
    try:
        bot.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        await ctx.send(f'```py\n{type(e).__name__}: {str(e)}\n```')
        return
    await ctx.send(f'{extension_name} loaded.')

@bot.command()
@commands.has_permissions(administrator = True)
async def unload(ctx, extension_name : str):
    '''Admin Only. Unloads an extension.'''
    bot.unload_extension('cogs.' + extension_name)
    await ctx.send(f'{extension_name} unloaded.')

@bot.command()
async def running(ctx):
    '''List currently loaded and running extensions.'''
    await ctx.send(f'```{[x[5:] for x in bot.extensions.keys()]}```')

@bot.command()
@commands.has_permissions(administrator = True)
async def reload(ctx, extension_name : str):
    '''Admin Only. Reloads an extension.'''
    bot.unload_extension(extension_name)
    await ctx.send(f'{extension_name} unloaded.')
    try:
        bot.load_extension('cogs.' + extension_name)
    except Exception as e:
        await ctx.send(f'```py\n{type(e).__name__}: {str(e)}\n```')
        return
    await ctx.send(f'{extension_name} loaded.')


for extension in startup_extensions:
    try:
        bot.load_extension('cogs.' + extension)
    except Exception as e:
        exc = f'{type(e).__name__}: {e}'
        root.info(f'Failed to load extension {extension}\n{exc}')
bot.run(token)