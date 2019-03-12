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

    @commands.command()
    @commands.has_role('gm')
    async def init(self, ctx, mode, *, initiative_list):
        '''Add user to initiative order with the given initiative result
        Initiative list should be formatted in a comma separated list:
        (e.g @user#1234 10, @member#4321 15, Big Monster 12, ...)
        
        Available modes are: 
        off - Deactivate tracking on this channel
        roundrobin - Everyone gets exactly one turn
        sr5 - One turn for every 10 points of initiative rolled'''

        simple_list = [x.strip for x in initiative_list.split(',')]

        entries = {}
        for e in simple_list:
            for t in e.split(' '):
                entries.update({' '.join(t[0:-1]): {'roll':t[-1], 'spent': 0, 'turns taken': 0}})

        self.initiative.update({str(ctx.channel.id):{'mode': mode, 'round': 0 , 'pass': 0, 'entries': entries}})

    async def get_next_turn(self, channel_id):
        ini = self.initiative.get(str(channel_id))

        mode = ini.get('mode')

        if mode == 'sr5':
            next = ('', 0)
            for e in ini.get('entries'):
                if e['roll'] - spent

        # round: #
        # pass: #
        # turns: [ID, Initiative, Spent]

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
        pass

    @commands.command()
    async def add(self, ctx, initiative, name = None):
        user = self.bot.get_user(name.strip('<@!>' ))
        if user == None: user = name
        self.initiative[ctx.guild.id].update({user:int(initiative)})


def setup(bot):
    bot.add_cog(Tracker(bot))
    log.info('Loaded!')