import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from discord.ext import commands
import logging
from common.classes import JsonFileObject
import discord

log = logging.getLogger(f'bot.{__name__}')

#Set this variable to the directory you would like to dump economy JSON files
data_dir = './data/economy/'

try:
    os.mkdir(os.path.abspath(data_dir))
except FileExistsError:
    pass


class Economy:
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def economy(self, ctx): 
        pass

    @economy.command()
    @commands.has_permissions(administrator = True)
    async def setcurrency(self, ctx, unit_name, *flags):
        '''Add or modify unit of currency to the list for this server. Possible flags include: limited, notrade, prefixunit=$'''
        pass

    @commands.command()
    async def give(self, ctx, user, amount, unit):
        pass

    @commands.command()
    async def check(self, ctx, unit):
        pass

    @commands.command()
    async def history(self, ctx, unit_name, lines = 5, user = None):
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
    log.info('Loaded!')
