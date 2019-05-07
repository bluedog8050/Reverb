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
data_dir = 'economy'

try:
    os.mkdir(os.path.abspath(data_dir))
except FileExistsError:
    pass


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.global_economy = JsonFileObject('economy.json')

    def get_local_tokens(self, ctx):
        tokens = self.global_economy.get(ctx.server)

        if not tokens:
            self.global_economy.update(ctx.server, {})
            tokens = self.global_economy[ctx.server]

        return tokens

    def get_token(self, ctx, name):
        tokens = self.get_local_tokens(ctx)
        token = tokens.get(name)

        if not token:
            tokens.update(name, {})
            token = tokens[name]
            token.update('ledger', {})

        return token

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def economy(self, ctx, *subcommand): 
        '''Update or add properties of a token.
        
        economy <token_name> <property> <value>'''

        name = subcommand[0]
        param = subcommand[1]
        value = subcommand[2]

        token = self.get_token(ctx, name)

        token.update(param, value)

    @commands.command()
    @commands.has_role('gm')
    async def setusermax(self, ctx, user, unit, max_value): 
        '''Set the maximum amount of a token for a single user
        
        setusermax <user> <token_name> <max_value>'''
        
        tokens = self.get_local_tokens(ctx)

        token = tokens.get(unit)

    @commands.command()
    @commands.has_role('gm')
    async def take(self, ctx, unit, user, max_value): 
        '''Work in Progress'''

    @commands.command()
    async def give(self, ctx, user, amount, unit):
        '''Work in Progress'''
        pass

    @commands.command()
    async def burn(self, ctx, user, amount, unit):
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
