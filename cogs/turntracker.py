import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import common.message_strings as mstr
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

        ini = self.initiative.get(str(message.channel.id))

        next = self.get_next_turn(message.channel.id)

        author = f'<@{message.author.id.replace("!","")}>'

        if author in next:
            ini['entries'][author]['turns taken'] += 1
        else:
            await message.delete()
            await message.channel.send(f'Sorry {message.author.mention}, you can only send a message when it is your turn! :smile:', delete_after = 15)

        await self.update_tracking_message(message.channel)

    async def update_tracking_message(self, channel):
        ini = self.initiative[str(channel.id)]
        mode = ini['mode']

        def is_waiting_msg(m):
            return m.content.startswith(mstr.PBP_WAITING)

        channel.purge(limit = 20, check = is_waiting_msg, bulk = False)

        if mode is not 'off':
            turn = self.get_next_turn(channel.id)
            try:
                turn = ' '.join(turn)
            except TypeError:
                pass
            msg = mstr.PBP_WAITING + '\n' + f"`Mode: {mode}`" + '\n' + turn
            await channel.send(msg)

    @commands.command()
    @commands.has_role('gm')
    async def init(self, ctx, mode, *initiative_list):
        '''Add user to initiative order with the given initiative result
        Initiative list should be formatted in a comma separated list:
        (e.g @user#1234 10, @member#4321 15, Big Monster 12, ...)
        
        Available modes are: 
        off - Deactivate tracking on this channel
        roundrobin - Everyone gets exactly one turn
        sr5 - One turn for every 10 points of initiative rolled'''

        simple_list = [x.strip() for x in ' '.join(initiative_list).replace('!','').split(',')]

        log.debug(simple_list)

        entries = {}
        for e in simple_list:
            t = e.split(' ')
            entries.update({' '.join(t[0:-1]): {'roll':t[-1], 'spent': 0, 'turns taken': 0}})

        log.debug(f'--> {entries}')

        self.initiative.update({str(ctx.channel.id):{'mode': mode, 'round': 0, 'pass': 0 , 'entries': entries}})

        log.debug(f'----> {self.initiative[str(ctx.channel.id)]}')

        await self.update_tracking_message(ctx.channel)

        await ctx.message.delete()

    def get_next_turn(self, channel_id):
        try:
            ini = self.initiative[channel_id]
        except KeyError:
            return None

        mode = ini['mode']

        entries = ini['entries']

        if mode is 'off':
            next = []

        elif mode is 'sr5':
            next = ('', 0)
            for i, e in entries:
                mod_ini = e['roll'] - e['spent'] - (10 * e['turns taken'])
                if mod_ini > 0 and mod_ini > next[1] and e['turns taken'] <= ini['pass']:
                    next = (i, mod_ini)
            if next is ('', 0):
                ini['pass'] += 1
                for i, e in entries:
                    mod_ini = e['roll'] - e['spent'] - (10 * e['turns taken'])
                    if mod_ini > 0 and mod_ini > next[1] and e['turns taken'] <= ini['pass']:
                        next = (i, mod_ini)
            if next is ('', 0):
                ini['round'] += 1
                ini['pass'] = 0
                for i, e in entries:
                    e['turns taken'] = 0
                    e['spent'] = 0
                    if e['roll'] > next[1]:
                        next = (i, e['roll'])
            if next is ('', 0):
                next = r'¯\_(ツ)_/¯'

        elif mode is 'roundrobin':
            next = []
            for i, e in entries:
                if e['turns taken'] <= ini['round']:
                    next.append(i)
            if not next:
                ini['round'] += 1
                if e['turns taken'] <= ini['round']:
                    next.append(i)
            if not next:
                next = [r'¯\_(ツ)_/¯']

        else:
            raise commands.CommandInvokeError('Invalid Initiative mode, use "off", "sr5", or "roundrobin"')

        return next

    @commands.command()
    async def skip(self, ctx, *users):
        '''Skips the named user(s) in initiative'''

        author_roles = [r.name for r in ctx.author.roles]

        if users and 'gm' not in author_roles:
            await ctx.send(f'Only a GM can name another person to skip, players should only use "{self.bot.command_prefix}skip" on it\'s own to skip themselves :smile:', delete_after = 15)
        elif not users:
            users = [f'<@{ctx.author.id}>']

        ch_id = str(ctx.channel.id)
        ini = self.initiative[ch_id]
        c_ini = self.get_next_turn(ch_id)
        user_list = [u.replace('!', '') for u in users]

        for user in user_list:
            if user in c_ini:
                ini[user]['turns taken'] += 1

        await self.update_tracking_message(ctx.channel)


def setup(bot):
    bot.add_cog(Tracker(bot))
    log.info('Loaded!')