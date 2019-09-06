import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from discord.ext import commands
import logging
import re
import configparser
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
        tokens = self.global_economy.get(ctx.server.id)

        if not tokens:
            self.global_economy.update(ctx.server.id, {})
            tokens = self.global_economy[ctx.server.id]
            self.global_economy.save()

        return tokens

    def get_token(self, ctx, name):
        tokens = self.get_local_tokens(ctx)
        token = tokens.get(name)

        if not token:
            tokens.update(name, {})
            token = tokens[name]
            token.update('ledger', {})
            self.global_economy.save()

        return token

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user \
        or message.content.startswith(self.bot.command_prefix):
            return
        
        #detect edge rolls and deduct edge automatically
        term = re.search(r'[.+!]')

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def economy(self, ctx, name = None, param = None, value = None): 
        '''Manage server currencies, use empty command to list available tokens and properties. Name only to create a new token or list all player balances.'''

        if not name:
            msg = '```'
            for token_name, token in self.get_local_tokens(ctx):
                msg += token_name + '\n'
                for key, item in token:
                    if not key == 'ledger':
                        msg += '\t{0}: \t{1}'.format(key, item)
                msg += '\n\n'
            msg += '```'
        elif name and not param:
            msg = '```'
            msg += name.capitalize() + '\n\n'
            for player, history in self.get_local_tokens(ctx)[name].get("ledger"):
                try:
                    player = 
                except:
                    pass
                msg += f''
                msg += '\n'
            msg += '```'
        else:
            token = self.get_token(ctx, name)

            if param and value:
                token.update(param, value)
                self.global_economy.save()

    @commands.command()
    @commands.has_role('gm')
    async def setmax(self, ctx, user, unit, max_value): 
        '''Set the maximum amount of a token for a single user.
        
        setmax <user> <token_name> <max_value>'''
        
        tokens = self.get_local_tokens(ctx)

        token = tokens.get(unit)

        if not token:
            return "Currency not found"

        token_user =  token.get(user.strip('<@!>'))

        token_user.update('max', max_value)

    @commands.command()
    @commands.has_role('gm')
    async def take(self, ctx, amount, unit, user, max_value): 
        '''GM Only. Remove an amount from a player\'s inventory'''
        

    @commands.command()
    async def give(self, ctx, user, amount, unit):
        '''WIP. Transfer an amount to another player. Currency must be tradable.'''
        pass

    @commands.command()
    async def burn(self, ctx, user, amount, unit):
        '''WIP. Spends tokens and lowers maximum by the same amount'''
        pass

    @commands.command()
    async def balance(self, ctx, unit, player = None):
        '''WIP. Shows account balance for self or another player'''
        pass

    @commands.command()
    async def history(self, ctx, unit_name, lines = 5, user = None):
        '''Work in Progress'''
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
    log.info('Loaded!')
