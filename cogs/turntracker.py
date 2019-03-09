import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from discord.ext import commands
from common.classes import JsonFileObject
import logging

log = logging.getLogger('bot.' + __name__)

gm_roles = ['gm','game master', 'dm', 'dungeon master', 'GM','Game Master', 'DM', 'Dungeon Master']
player_roles = ['player', 'players']

class Tracker:
    def __init__(self, bot):
        self.bot = bot
        self.initiative = JsonFileObject('initiative.json')
    async def on_message(self, message):
        if message.author == self.bot.user \
            or message.content.startswith(self.bot.command_prefix):
            return
        log.debug('message received')

    async def get_next_turn(guild_id, channel_id):
        guild_ini = self.initiative.get(str(guild_id))
        ini = guild_ini.get(str(channel_id))

        turn = {}

        #TODO: generate passes from initial rolls, minus penalties, minus 10 per pass
        
        #TODO: sort list, get highest value for pass

        return turn



    @commands.command()
    @commands.has_any_role(gm_roles)
    async def roundrobin(self, ctx, *groups):
        '''Starts turn tracking on this channel with the listed groups or individuals'''
        pass

    @commands.command()
    @commands.has_any_role(gm_roles)
    async def untrack(self, ctx):
        '''Turns off turn tracking for this channel'''
        pass

    @commands.command()
    async def skip(self, ctx, *users):
        '''Skips the current or named user(s)'''
        pass

    @commands.command()
    async def sr5combat(self, ctx):
        if self.mode == 'roundrobin':
            self.mode = 'combat'
        else:
            self.mode = 'roundrobin'

    @commands.command()
    async def add(self, ctx, initiative, name = None):
        user = self.bot.get_user(name.strip('<@!>' ))
        if user == None: user = name
        self.initiative[ctx.guild.id].update({user:int(initiative)})


def setup(bot):
    bot.add_cog(Tracker(bot))
    log.info('Loaded!')