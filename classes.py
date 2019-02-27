import discord
import re
import json
from datetime import datetime
from configparser import ConfigParser
from functions import get_members_from_role

#region SECTION COMMAND CLASSES
class CommandError(KeyError):
    pass

class CommandPacket():
    '''Parse and package a message containing a command and expose commonly used attributes from message class'''
    def __init__(self, config, message : discord.Message):
        if message.server.id not in config:
            config[message.server.id] = {}
            config[message.server.id]['server_name'] = message.server.name
        if not message.content.startswith(config[message.server.id].get('command_char')): 
            raise CommandError('Message does not start with designated command character')
        self.message = message
        self.server = message.server
        self.channel = message.channel
        self.content = message.content
        self.args = [x.strip() for x in self.content.split()]
        self.sender = self.message.author
        self.command = self.args.pop(0).strip(config[message.server.id].get('command_char'))

    def __getitem__(self, index):
        return self.args[index]

    def read(self, number_words : int, start_index : int = 0):
        _list = []
        for i in range(start_index, start_index + number_words + 1):
            _list.append(self.args[i])
        _string = ' '.join(_list)
        return _string

    async def getTargetMembers(self):
        m = self.target_members = re.findall(r'<?@!?(&?\d+)>?', self.content)
        to_add = []
        to_remove = []
        #expand out role to users
        for t in m:
            if t.startswith('&'):
                to_remove.append(t)
                to_add.extend(get_members_from_role(self.server, t))
        for t in to_remove:
            m.remove(t)
        for t in m:
            yield t

    async def getTargetChannels(self):
        for t in re.findall(r'<?#(\d+)>?', self.content):
            yield t

class Bot():
    def __init__(self):
        self._registry = {}
    def command(self, *permissions):
        '''Register a function as a chat command. Function must return a string'''
        def wrapper(func):
            self._registry[func.__name__] = (func, list(permissions))
            return func
        return wrapper
    async def do(self, config, cmd : CommandPacket):
        if cmd.command == 'help':
            return await self.help(config, cmd)
        elif cmd.command not in self._registry:
            raise CommandError('No registered function matches given command')
        elif not self._registry[cmd.command][1]: #if no set permissions
            return await self._registry[cmd.command][0](cmd) #just do it
        elif not cmd.args and 'self' in self._registry[cmd.command][1]:
            return await self._registry[cmd.command][0](cmd)
        elif 'player' in self._registry[cmd.command][1] and config[cmd.server.id]['player_role'] in [r.name for r in cmd.sender.roles]:
            return await self._registry[cmd.command][0](cmd)
        elif 'gm' in self._registry[cmd.command][1] and config[cmd.server.id]['gm_role'] in [r.name for r in cmd.sender.roles]:
            return await self._registry[cmd.command][0](cmd)
        else:
            if not self._registry[cmd.command][1]:
                return await self._registry[cmd.command][0](cmd)
            for permission in self._registry[cmd.command][1]:
                for role in cmd.sender.roles:
                    if role.name == permission:
                        try:
                            return await self._registry[cmd.command][0](cmd)
                        except KeyError:
                            raise CommandError('No registered function matches given command')
                else:
                    raise CommandError(f'User does not have required permissions for command "{cmd.command}"')
    async def help(self, config, cmd):
        l = []
        for n,d in self._registry.items():
            if '<admin-only>' in d:
                continue
            try:
                line = '```' + config.get(cmd.server.id, 'command_char') + '{0} {1}```\n{2}{3}'.format(n, d[0].__annotations__['return'], '*' + str(d[1]) + '* - ' if d[1] else '', d[0].__doc__.format(wiki = config.get(cmd.server.id, 'wikia_list')))
            except KeyError:
                line = '```' + config.get(cmd.server.id, 'command_char') + '{0}```\n{1}{2}'.format(n, '*' + str(d[1]) + '* - ' if d[1] else '', d[0].__doc__.format(wiki = config.get(cmd.server.id, 'wikia_list')))
            l.append(line)
        return 'Commands available to Reverb:\n\n' + '\n\n'.join(l)
#endregion !SECTION

#SECTION Ledger Class
class Ledger:
    SUCCESS = 'Ledger updated! :thumbsup:'
    ERROR = ':frown: Something went wrong while updating the ledger...'

    ## {'server':{'user':['oct-18-2018',1,2,'This is a test entry']},}
    def __init__(self, name, unit_string, *flags):
        self.name = name
        self.unit_string = unit_string
        try:
            with open(f'{self.name}.json') as f:
                self.data = json.load(f)
        except:
            self.data = {}
        if 'prefix' in flags: self.prefix = True 
        else: self.prefix = False
        if 'allow_negative' in flags: self.allow_negative = True 
        else: self.allow_negative = False
        
        return

    # SERVER > USER > [date, change, balance, note],
    #ANCHOR ADD ENTRY
    def addentry(self, server, user, amount_change, note=''):
        # try:    
        if server not in self.data: self.data.update({server : {}})
        if user not in self.data[server]: self.data[server].update({user : []})
        try:
            balance = int(self.data[server][user][-1][2])+int(amount_change)
        except:
            balance = int(amount_change)
        entry = [datetime.datetime.now().strftime(r"%Y-%m-%d"), str(amount_change), str(balance), note]
        print(entry)
        self.data[server][user].append(entry)
        message = Ledger.SUCCESS
        # except:
        #     print('Ledger failed to add item!')
        #     message = Ledger.error

        return message
    #ANCHOR GET BALANCE
    def getbalance(self, server, user, *flags):
        try:
            print(self.data)
            if 'int' in flags:
                balance = int(self.data[server][user][-1][2])
            else:
                balance = (self.unit_string + self.data[server][user][-1][2]) if self.prefix else (self.data[server][user][-1][2] + ' ' + self.unit_string)
        except KeyError:
            if 'int' in flags:
                balance = 0
            else:
                balance = 'no transaction history'
        return balance
    #ANCHOR SAVE TO FILE
    def savetofile(self):
        try:
            with open(f'{self.name}.json', 'w+') as outfile:
                json.dump(self.data, outfile)
            print('{0} ledger saved'.format(self.unit_string))
        except:
            print('{} ledger could not be saved to file!'.format(self.unit_string))
            return
    #ANCHOR GET HISTORY
    def gethistory(self, server, user, lines=5):
        history = 'Date\t\tChange\tBal\tNote\n-------------------------------------\n'
        for i in range(1, int(lines) + 1):
            try:
                history = history + str(self.data[server][user][-i]) + '\n'
            except:
                break
        history = history.replace(', ',',\t').replace('\'', '').replace('[','').replace(']','')
        return history
    #ANCHOR TRANSFER
    def transfer(self, server, sender, recipients : list, amount, note):
        if int(amount) * len(recipients) > self.getbalance(server, sender, 'int'):
            pass
            #await client.send_message()
#!SECTION 