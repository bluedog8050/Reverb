import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import common.message_strings as mstr
from discord.ext import commands
from common.classes import JsonFileObject
import logging
import random

log = logging.getLogger('bot.' + __name__)

# gm_roles = ['gm','game master', 'dm', 'dungeon master', 'GM','Game Master', 'DM', 'Dungeon Master']
# player_roles = ['player', 'players']

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initiative = JsonFileObject('initiative.json')
    def _is_waiting_msg(self, m):
            return m.content.startswith(mstr.PBP_WAITING)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or self._is_waiting_msg(message):
            return
        elif message.content.startswith(self.bot.command_prefix):
            return

        ini = self.initiative.get(str(message.channel.id))

        if not ini:
            return

        next = await self.get_next_turn(message)

        author = message.author.mention.replace("!","")

        if not next:
            pass
        elif author in next:
            ini['entries'][author]['turns taken'] += 1
            self.initiative.save()
        elif author not in next:
            await message.delete()
            await message.channel.send(f'Sorry {message.author.mention}, you can only send a message when it is your turn! :slight_smile:', delete_after = 15)

        await self.update_tracking_message(message)

    async def update_tracking_message(self, ctx):
        ini = self.initiative[str(ctx.channel.id)]

        turn = await self.get_next_turn(ctx)
        mode = ini['mode']

        if mode == 'off':
            return

        _round = str(ini['round'] + 1)
        _pass = str(ini['pass'] + 1) if mode == 'sr5' else 0
        log.debug(f'Turn = {turn}')

        if isinstance(turn, list):
            turn = '\t'.join(turn)

        msg = mstr.PBP_WAITING
        msg += '\n' + f'`Round: {_round}'
        if _pass: msg +=  f' | Pass: {_pass}'
        msg +=  f' | Mode: {mode}`'
        msg += '\n \n' + turn

        await ctx.channel.purge(check = self._is_waiting_msg)
        await ctx.channel.send(msg)

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

        log.debug(f'{len(initiative_list)} Entries passed: {initiative_list}')

        entries = {}
        if mode == 'sr5':
            simple_list = [x.strip() for x in ' '.join(initiative_list).replace('!','').split(',')]
            for e in simple_list:
                t = e.split(' ')
                entries.update({' '.join(t[0:-1]): {'formula': t[-1], 'roll': 0, 'spent': 0, 'turns taken': 0}})
            log.debug(simple_list)
        elif mode == 'roundrobin':
            for e in initiative_list:
                entries.update({e: {'turns taken': 0}})

        log.debug(f'--> {entries}')

        self.initiative.update({str(ctx.channel.id):{'mode': mode, 'round': 0, 'pass': 0 , 'entries': entries}})

        log.debug(f'----> {self.initiative[str(ctx.channel.id)]}')

        await self._roll(ctx)
        await self.update_tracking_message(ctx)

    @commands.command()
    @commands.has_role('gm')
    async def setinit(self, ctx, user, formula = None):
        '''Set formula for or add a user to turn tracking'''

        player = user.replace('!','')
        ini = self.initiative.get(str(ctx.channel.id))

        #sanity check
        if not ini or ini['mode'] == 'off':
            await ctx.send(f'Unable to update user initiative because turn tracking is not active on this channel. Use `{self.bot.command_prefix}init` to activate turn tracking.', delete_after = 15)
            return

        entries = ini['entries']

        if ini['mode'] == 'sr5':
            if formula == None:
                await ctx.send('Unable to update user initiative. A formula is required for sr5 initiative in the format `x+yd6`', delete_after = 15)
            else:
                if entries.get(player):
                    entries[player]['formula'] = formula
                else:
                    entries.update({player: {'formula': formula, 'roll': 0, 'spent': 0, 'turns taken': 0}})
            return

        if ini['mode'] == 'roundrobin':
            entries.update({player: {'formula': formula, 'roll': 0, 'spent': 0, 'turns taken': ini['round'] - 1}})

        await self._roll(ctx, player)
        await self.update_tracking_message(ctx)

    @commands.command()
    @commands.has_role('gm')
    async def reroll(self, ctx, *users):
        '''[sr5 only] Re-roll initiative for any selected user without disturbing other entries in the order. Name no players to reroll everyone.'''
        players = [x.replace('!','') for x in users]
        await self._roll(ctx, *players)

    async def _roll(self, ctx, *players):
        ini = self.initiative[str(ctx.channel.id)]
        done = []
        failed = []

        try:
            log.debug(f'_roll called by {ctx.command}')
        except Exception as e:
            log.debug(f'_roll called by a process: {e}')

        #only need to re-roll when mode is Shadowrun 5th edition
        if ini['mode'] != 'sr5':
            return

        #if no entries are listed, reroll all of them
        if not players: entries = ini['entries']
        else: entries = {p:ini['entries'].get(p) for p in players}

        for k, e in entries.items():
            try:
                log.debug(f'Rolling for {k} ---> {e}')
                formula = e['formula']
                log.debug(f'Formula: {formula}')
                mod, pattern = formula.split('+')
                count, die = pattern.split('d')
                rolls = random.choices([x + 1 for x in range(int(die))], k = int(count))
                log.debug(f'Dice Rolls: {rolls}')
                roll_sum = sum(rolls)
                grand_total = int(mod) + roll_sum
                log.debug(f'Final roll: {mod} + {roll_sum} = {grand_total}')
                e['roll'] = grand_total
                done.append(f"{k}\t{e['roll']}")
            except Exception as f:
                failed.append(f"{k}, {f}")

        await ctx.channel.send('```Initiative has been rolled:```{0}'.format('\n'.join(done)))
        
        if failed:
            await ctx.channel.send('```The following entries had errors and could not be rolled:``` {0}'.format('\n'.join(failed)))

        #TODO: Send confirmation message with list of initiative rolls

        self.initiative.save()
        await self.update_tracking_message(ctx)

    async def get_next_turn(self, ctx):
        try:
            ini = self.initiative[str(ctx.channel.id)]
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
                await self._roll(ctx)
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
        '''Skips the named user(s) in initiative. If no users named, skips self'''

        author_roles = [r.name for r in ctx.author.roles]

        if users and 'gm' not in author_roles:
            await ctx.send(f'Only a GM can name another person to skip, players should only use "{self.bot.command_prefix}skip" on it\'s own to skip themselves :smile:', delete_after = 15)
            return
        elif not users:
            users = [ctx.author.mention]

        ch_id = str(ctx.channel.id)
        ini = self.initiative[ch_id]
        c_ini = await self.get_next_turn(ctx)
        user_list = [u.replace('!', '') for u in users]

        for user in user_list:
            if user in c_ini:
                ini['entries'][user]['turns taken'] += 1
                self.initiative.save()
                await ctx.send(f'`Skipped` {user}')

        await ctx.message.delete()
        await self.update_tracking_message(ctx)

    @commands.command()
    async def spendinit(self, ctx, amount : int, *, action_taken):
        '''Spend initiative points to inturrupt or take a special action'''

        author = ctx.author.mention.replace('!','')
        ini = self.initiative[str(ctx.channel.id)]
        entries = ini['entries']
        entry = entries[author]
        cpass = ini['pass']
        roll = entry['roll']
        spent = entry['spent']
        net_init = roll - spent - (10 * cpass)

        if net_init >= amount:
            entry['spent'] += amount
            new_init = net_init - amount
            self.initiative.save()
            await ctx.send(f'{author} spent {amount} initiative to take the following action. Their initiative is now **{new_init}** \n \n {action_taken}')
        else:
            await ctx.send(f'Sorry, {author}, you do not have the enough initiative to spend. Your current score is **{net_init}**.', delete_after = 15)
        
        await ctx.message.delete()
        await self.update_tracking_message(ctx)

    @commands.command()
    @commands.has_role('gm')
    async def takeinit(self, ctx, user, amount : int, *, action_taken):
        '''Same as spendinit but used on a user or NPC other than self'''

        author = user.replace('!', '')
        ini = self.initiative[str(ctx.channel.id)]
        entries = ini['entries']
        entry = entries[author]
        cpass = ini['pass']
        roll = entry['roll']
        spent = entry['spent']
        net_init = roll - spent - (10 * cpass)

        if net_init >= amount:
            entry['spent'] += amount
            new_init = net_init - amount
            self.initiative.save()
            await ctx.send(f'{author} spent {amount} initiative to take the following action. Their initiative is now **{new_init}** \n \n {action_taken}')
        else:
            await ctx.send(f'Sorry, {author} does not have the enough initiative to spend. Their current score is **{net_init}**.', delete_after = 15)

        await ctx.message.delete()
        await self.update_tracking_message(ctx)

    @commands.command()
    async def taketurn(self, ctx, user, *, action_taken):
        '''Allows a person to take a turn for an NPC or player. User argument only required for round robin'''

        ini = self.initiative.get(str(ctx.channel.id))
        cini = await self.get_next_turn(ctx)

        #if mode is not round robin, attach the user argument to the beginning of action string since it should be ignored
        if ini['mode'] != 'round robin': 
            action_taken = f'{user} {action_taken}'
            user = cini.split('(')[0].strip() #current initiative minus the initiative score
        
        player = user.replace('!', '')
        entries = ini['entries']
        entry = entries[player]

        if player in cini:
            entry['turns taken'] += 1
            self.initiative.save()
            await ctx.send(action_taken)
        else:
            await ctx.send(f'Sorry, {player} does not have a turn to take right now', delete_after = 15)

        await ctx.message.delete()
        await self.update_tracking_message(ctx)

    @commands.command()
    @commands.has_role('gm')
    async def addroll(self, ctx, user, roll : int = 0):
        '''Set an individuals initiative roll. If round robin, this will cause the player to join the next round'''

        player = user.replace('!', '')
        ini = self.initiative[str(ctx.channel.id)]
        entries = ini['entries']

        if ini['mode'] == 'off':
            await ctx.send(f'{player} could not be added because turn tracking is turned off. Use `{self.bot.command_prefix}init` to start turn tracking. Type `{self.bot.command_prefix}help init` for more detailed information', delete_after = 15)
            return

        if ini['mode'] == 'sr5':
            entries.update({player: {'roll': roll, 'spent': roll, 'turns taken': 0}})
        elif ini['mode'] == 'roundrobin':
            entries.update({player: {'turns taken': ini['round']}})

        await ctx.send(f'{player} has been added to initiative. They will join in starting next round.', delete_after = 15)

        self.initiative.save()

        await ctx.message.delete()
        await self.update_tracking_message(ctx)

def setup(bot):
    bot.add_cog(Tracker(bot))
    log.info('Loaded!')