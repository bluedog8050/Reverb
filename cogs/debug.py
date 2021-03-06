import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from discord.ext import commands
import logging
import re
import discord

'''Basic Debug utilities to make sure I am doing things right'''

__version__ = '2.01a'

log = logging.getLogger('bot.' + __name__)

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def version(self, ctx):
        '''Prints discord.py version being used'''
        version = f'Reverb: v{__version__}' + '\n' + f'discord.py: {discord.version_info}'
        await ctx.send(version)
    @commands.command()
    async def ping(self, ctx):
        '''Ping for response'''
        await ctx.send('Pong!')
    @commands.command()
    async def echo(self, ctx, *, message):
        '''Echo a string'''
        if message.startswith('<#'):
            regex = re.search(r'^<#(\d+)> (.+)', message)
            await self.bot.get_channel(int(regex.group(1))).send(regex.group(2))
        else:
            await ctx.send(message)
        await ctx.message.delete()
    @commands.command()
    async def echodm(self, ctx, *, message):
        '''Echo a string as direct message'''
        await ctx.author.send(message)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Debug(bot))
    log.info('Loaded!')