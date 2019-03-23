import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from discord.ext import commands
import logging
from common.classes import Ledger
import discord

log = logging.getLogger(f'bot.{__name__}')

#Set this variable to the directory you would like to dump economy JSON files
data_dir = './data/economy/'

try:
    os.mkdir(os.path.abspath(data_dir))
except FileExistsError:
    pass


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ledgers = {}
        currency_list = os.listdir(os.path.abspath(data_dir))

        for c in currency_list:
            try:
                self.ledgers.update(c, Ledger(data_dir, c, c))
                log.info(f'{c} Ledger loaded')
            except:
                log.info(f'{c} Ledger could not be loaded')

    @commands.group()
    @commands.has_permissions(administrator = True)
    async def economy(self, ctx, *subcommand): 
        '''Work in Progress'''

        if subcommand:
            if subcommand[0] == 'set':
                pass

    @commands.command()
    async def give(self, ctx, user, amount, unit):
        '''Work in Progress'''
        pass

    @commands.command()
    async def balance(self, ctx, unit):
        '''Work in Progress'''
        pass

    @commands.command()
    async def history(self, ctx, unit_name, lines = 5, user = None):
        '''Work in Progress'''
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
    log.info('Loaded!')
