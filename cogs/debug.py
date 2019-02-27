from discord.ext import commands
import logging
import re
import discord

log = logging.getLogger(__name__)

'''Basic Debug utilities to make sure I am doing things right'''

class Debug():
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def version(self, ctx):
        '''Prints discord.py version being used'''
        await ctx.send(discord.version_info)
    @commands.command()
    async def ping(self, ctx):
        '''Ping for response'''
        await ctx.send('Pong!')
    @commands.command()
    async def echo(self, ctx, *, message):
        '''Echo a declared string'''
        if message.startswith('<#'):
            regex = re.search(r'^<#(\d+)> (.+)', message)
            await self.bot.get_channel(int(regex.group(1))).send(regex.group(2))
        else:
            await ctx.send(message)

def setup(bot):
    bot.add_cog(Debug(bot))
    log.info('Loaded!')