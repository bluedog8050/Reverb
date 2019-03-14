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
    def _is_waiting_msg(self, m):
            return m.content.startswith(mstr.PBP_WAITING)
    async def on_message(self, message):
        if message.author == self.bot.user or self._is_waiting_msg(message):
            return
        elif message.content.startswith(self.bot.command_prefix):
            await message.delete()
            await self.update_tracking_message(message.channel)
            return

        ini = self.initiative.get(str(message.channel.id))

        next = self.get_next_turn(message.channel.id)

        author = message.author.mention.replace("!","")

        if not next:
            return

        if author in next:
            ini['entries'][author]['turns taken'] += 1
            self.initiative.save()
        else:
            await message.delete()
            await message.channel.send(f'Sorry {message.author.mention}, you can only send a message when it is your turn! :slight_smile:', delete_after = 15)

        await self.update_tracking_message(message.channel)

    async def update_tracking_message(self, channel):
        ini = self.initiative[str(channel.id)]

        await channel.purge(check = self._is_waiting_msg)

        turn = self.get_next_turn(channel.id)
        mode = ini['mode']

        if mode == 'off':
            return

        _round = str(ini['round'] + 1)
        _pass = str(ini['pass'] + 1) if mode == 'sr5' else 0
        log.debug(f'Turn = {turn}')

        if isinstance(turn, list):
            turn = '    '.join(turn)

        msg = mstr.PBP_WAITING
        msg += '\n' + f'`Round: {_round}'
        if _pass: msg +=  f' | Pass: {_pass}'
        msg +=  f' | Mode: {mode}`'
        msg += '\n \n' + turn

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

        #sanity check
        valid_modes = ['sr5', 'roundrobin', 'off']
        if mode not in valid_modes:
            await ctx.send(f'Invalid mode used, please use one of the following: {valid_modes}. (eg. `{self.bot.command_prefix}init roundrobin @user#1234...`)', delete_after = 10)
            return

        simple_list = [x.strip() for x in ' '.join(initiative_list).replace('!','').split(',')]

        log.debug(simple_list)

        entries = {}
        for e in simple_list:
            if mode == 'sr5':
                t = e.split(' ')
                entries.update({' '.join(t[0:-1]): {'roll':int(t[-1]), 'spent': 0, 'turns taken': 0}})
            elif mode == 'roundrobin':
                entries.update({e: {'turns taken': 0}})

        log.debug(f'--> {entries}')

        self.initiative.update({str(ctx.channel.id):{'mode': mode, 'round': 0, 'pass': 0 , 'entries': entries}})

        log.debug(f'----> {self.initiative[str(ctx.channel.id)]}')

        self.initiative.save()

        await self.update_tracking_message(ctx.channel)

    def get_next_turn(self, channel_id):
        try:
            ini = self.initiative[str(channel_id)]
        except KeyError:
            return None

        mode = ini['mode']

        entries = ini['entries']

        if mode == 'off':
            next = ''

        elif mode == 'sr5':
            highest = ('', 0)
            for i, e in entries.items():
                mod_ini = e['roll'] - e['spent'] - (10 * e['turns taken'])
                if mod_ini > 0 and mod_ini > highest[1] and e['turns taken'] <= ini['pass']:
                    highest = (i, mod_ini)
            if highest == ('', 0):
                ini['pass'] += 1
                for i, e in entries.items():
                    mod_ini = e['roll'] - e['spent'] - (10 * e['turns taken'])
                    if mod_ini > 0 and mod_ini > highest[1] and e['turns taken'] <= ini['pass']:
                        highest = (i, mod_ini)
                self.initiative.save()
            if highest == ('', 0):
                ini['round'] += 1
                ini['pass'] = 0
                for i, e in entries.items():
                    e['turns taken'] = 0
                    e['spent'] = 0
                    if e['roll'] > highest[1]:
                        highest = (i, e['roll'])
                self.initiative.save()
            if highest == ('', 0):
                next = r'¯\_(ツ)_/¯'
            else: 
                next = f'{highest[0]} ({str(highest[1])})'

        elif mode == 'roundrobin':
            next = []
            for i, e in entries.items():
                if e['turns taken'] <= ini['round']:
                    next.append(i)
            if not next:
                ini['round'] += 1
                if e['turns taken'] <= ini['round']:
                    next.append(i)
                self.initiative.save()
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
                ini['entries'][user]['turns taken'] += 1
                self.initiative.save()

    # @commands.command()
    #     async def spendinit(self, ctx, amount, *description):
    #         author = ctx.author.mention.replace('!','')
    #         entry = self.initiative.get
    #         if 

def setup(bot):
    bot.add_cog(Tracker(bot))
    log.info('Loaded!')