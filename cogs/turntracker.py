from discord.ext import commands
import logging

log = logging.getLogger(__name__)

gm_roles = ['gm','game master', 'dm', 'dungeon master', 'GM','Game Master', 'DM', 'Dungeon Master']
player_roles = ['player', 'players']

class Tracker:
    def __init__(self, bot):
        self.bot = bot
        self.mode = 'roundrobin'
        self.initiative = {}
    async def on_message(self, ctx):
        log.debug('message received')
    @commands.command()
    @commands.has_any_role(gm_roles)
    async def track(self, ctx, *groups):
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
    async def combat(self, ctx):
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