#!/home/pi/reverb/bin/python3
'''Reverb Bot is a chat command bot created for use with Discord. The primary purpose
of this program is to assist in a "play by post" roleplaying game on a text or voice 
chat server.

    Copyright (C) 2018  Derek Peterson < deniableassetsgm@gmail.com >

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.'''

import asyncio
import datetime
import html
import json
import os
import re
import sys
import types
import configparser
import uptime as Uptime
from collections import Counter
from collections import OrderedDict

import discord
import wikia
import uptime as UptimeModule

import message_strings as mstr

#SECTION CONFIG VARIABLES
COMMAND_CHAR = '!'
GM_ROLE = 'gm'
PLAYER_ROLE = 'player'
SUB_WIKIA = ['shadowrun']
#!SECTION

#Print Copyright disclaimer
print('''Reverb Bot  Copyright (C) 2018  Derek Peterson
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; see LICENSE file for more information.''')

#set CWD and load system.config settings
os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))

config = configparser.ConfigParser(default_section='DEFAULT', allow_no_value=True, dict_type=OrderedDict)
books = configparser.ConfigParser()

def save_config():
    with open('bot.ini', 'w+') as f:
        f.write(mstr.SYSTEM_CONFIG_BOILERPLATE)
        f.write('\n')
        config.write(f)

try:
    with open('bot.ini', 'r') as f:
        config.read_file(f)
except FileNotFoundError:
    #Write default bot.ini
    config['DEFAULT'] = {}
    defconfig = config['DEFAULT']
    defconfig['command_char'] = '!'
    defconfig['gm_role'] = 'gm'
    defconfig['player_role'] = 'player'
    defconfig['wikia_list'] = 'shadowrun'
    save_config()

try:
    with open('ref_books.ini') as f:
        books.read_file(f)
except FileNotFoundError:
    data = '''# [TAG]
#    title = Full Title of the Book
#    url = http://www.mywebsite.com/directory/books/pg{page}.pdf
#    offset = 2  #to correct differences between page number and file number'''
    with open('ref_books.ini', 'w+') as f:
        f.write(data)

print('script started in:', os.getcwd())
time_start = datetime.datetime.utcnow()

client = discord.Client()
links = {}
pbp_tracker = {}

try:
    with open('bot.key', 'r') as k:
        bot_token = k.read()
except:
    print(mstr.NO_KEY_FILE)
    print('Exiting script...')
    exit(0)

def read_json_file(filename, default_data = r'{}'):
    try:
        with open(filename, 'r+') as f:
            return json.load(f)
    except:
        with open(filename, 'a+') as f:
            f.write(default_data)
            return dict(default_data)

links = read_json_file('links.json')
pbp_tracker = read_json_file('pbp.json')
command_stats = read_json_file('cmd_stats.json')

#books: {REF:[FolderURL,PgOffset]}

global clear_flag
clear_flag = []

async def delete_messages(self, msg_list):
    for msg in msg_list:
        await client.delete_message(msg)
        await asyncio.sleep(1.2)

#region SECTION COMMAND CLASSES
class CommandError(KeyError):
    pass
class CommandPacket():
    '''Parse and package a message containing a command and expose commonly used attributes from message class'''
    def __init__(self, message : discord.Message):
        if message.server.id not in config:
            config[message.server.id] = {}
            config[message.server.id]['server_name'] = message.server.name
            save_config()
        if not message.content.startswith(config[message.server.id].get('command_char')): 
            raise CommandError('Message does not start with designated command character')
        self.message = message
        self.server = message.server
        self.channel = message.channel
        self.content = message.content
        self.args = [x.strip() for x in self.content.split()]
        self.sender = self.message.author
        self.command = self.args.pop(0)[1:]
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
                to_add.extend(getMembersFromRole(self.server, t))
        for t in to_remove:
            m.remove(t)
        for t in m:
            yield t
    async def getTargetChannels(self):
        for t in re.findall(r'<?#(\d+)>?', self.content):
            yield t
class Bot():
    def __init__(self):
        self.registry = {}
    def command(self, *permissions):
        '''Register a function as a chat command. Function must return a string'''
        def wrapper(func):
            setattr(wrapper,'__name__', func.__name__)
            self.registry[func.__name__] = (func, list(permissions))
            return func
        return wrapper
    async def do(self, command : CommandPacket):
        if command.command == 'help':
            return await self.help(command)
        elif command.command not in self.registry:
            raise CommandError('No registered function matches given command')
        elif not self.registry[command.command][1]: #if no set permissions
            return await self.registry[command.command][0](command) #just do it
        elif not command.args and 'self' in self.registry[command.command][1]:
            return await self.registry[command.command][0](command)
        elif 'player' in self.registry[command.command][1] and config[command.server.id]['player_role'] in [r.name for r in command.sender.roles]:
            return await self.registry[command.command][0](command)
        elif 'gm' in self.registry[command.command][1] and config[command.server.id]['gm_role'] in [r.name for r in command.sender.roles]:
            return await self.registry[command.command][0](command)
        else:
            if not self.registry[command.command][1]:
                return await self.registry[command.command][0](command)
            for permission in self.registry[command.command][1]:
                for role in command.sender.roles:
                    if role.name == permission:
                        try:
                            return await self.registry[command.command][0](command)
                        except KeyError:
                            raise CommandError('No registered function matches given command')
                else:
                    raise CommandError(f'User does not have required permissions for command "{command.command}"')
    async def help(self, command):
        l = []
        for n,d in self.registry.items():
            try:
                line = '```' + config.get(command.server.id, 'command_char') + '{0} {1}```\n{2}{3}'.format(n, d[0].__annotations__['return'], '*' + str(d[1]) + '* - ' if d[1] else '', d[0].__doc__.format(wiki = config.get(command.server.id, 'wikia_list')))
            except KeyError:
                line = '```' + config.get(command.server.id, 'command_char') + '{0}```\n{1}{2}'.format(n, '*' + str(d[1]) + '* - ' if d[1] else '', d[0].__doc__.format(wiki = config.get(command.server.id, 'wikia_list')))
            l.append(line)
        return 'Commands available to Reverb:\n\n' + '\n\n'.join(l)
#endregion !SECTION

bot = Bot()

#region SECTION Command List
#ANCHOR HELP
@bot.command()
async def help(command):
    '''Lists available commands and their help text'''
    pass #Placeholder function to add help text to builtin help command

@bot.command()
#ANCHOR REVERB VERSION
async def version(command):
    '''Echo the version number of discord.py in use'''
    v = discord.__version__
    print('discord.py ' + v)
    return 'Discord.py ' + v

@bot.command()
#ANCHOR REVERB UPTIME
async def uptime(command):
    '''Echo how long since the bot's last reboot'''
    msg = get_uptime()
    print(msg)
    return msg

@bot.command()
#ANCHOR SYSUPTIME
async def sysuptime(command):
    '''Echo how long since the last OS reboot'''
    msg = get_sysuptime()
    print(msg)    
    return msg

#ANCHOR REVERB
@bot.command('gm')
async def reverb(command) -> '@tag #destination':
    '''Copy messages from @tag in this channel to #destination channel. \'all\' may be used to echo all messages'''
    if command.args[0].lower() == 'all':
        command.args.pop(0) #pop out all keyword
        s = add_link(command.server.id,command.channel.id,'all', command.args[0])

        print(s)
        
        if s is mstr.UPDATE_SUCCESS:
            return '{0} Now forwarding all messages in <#{1}> to <#{2}>'.format(s, command.channel.name, command.args[0])
        else:
            return s

        save_links()
    else:
        s = add_link(command.server.id, command.channel.id, command.args[0], command.args[1])
        if s is mstr.UPDATE_SUCCESS:
            return '{0} Forwarding all messages in <#{1}> from <@{2}> to <#{3}>'.format(s, command.channel.id, command.args[0], command.args[1])
        else:
            await client.send_message(command.channel, s)
        return

#ANCHOR TRACK
@bot.command('gm')
async def track(command) -> '@group ...':
    '''Begin Play-by-Post turn tracking in current channel. Each group takes their turn together. A Group can be a @member#0000 or @role'''
    cmd_groups = command.args
    grp_members = []
    all_members = []
    for role in cmd_groups:
        members = {}
        for member in getMembersFromRole(command.server, role):
            members[member] = False
            member_object = command.server.get_member(member)
            all_members.append(member_object.nick if member_object.nick else member_object.name)
        grp_members.append(members)
    pbp_tracker[command.channel.id] = []
    for group in grp_members:
        pbp_tracker[command.channel.id].append(group)
    await check_pbp(command.message)
    return mstr.PBP_STARTED.format(groups=cmd_groups,members=all_members)

#ANCHOR SKIP
@bot.command('gm', 'self')
async def skip(command) -> '[@tag ...]':
    '''While using PBP tracking: skip @tag this turn. Provide no player tag to skip your own turn this round. Tag may be a @member#0000 or @role'''
    command.args.pop(0) #pop command keyword out of list
    players = command.args #the rest of args should be players or roles
    p_to_append = set()
    p_to_pop = set()
    for p in players:
        p = p.replace('<@','').replace('!','').replace('>','')
        if re.search(r'&?\w+',p): #search for role
            for m in getMembersFromRole(command.server, p):
                p_to_append.add(m)
            p_to_pop.add(p) #either role name or invalid entry, either way it needs to go now
    players = list(set(players) - (p_to_pop + p_to_append))
    
    instance = pbp_tracker[command.channel.id]
    i = 0
    has_members_left = False

    for group in instance:
        for member in group.keys():
            if not group[member]:
                has_members_left = True
                break
        if has_members_left:
            break
        else:
            i += 1
    for k in instance[i].keys():
        if k in players:
            instance[i][k] = True
    
#ANCHOR UNTRACK
@bot.command('gm')
async def untrack(command):
    '''Stop Play-by-Post turn tracking for this channel'''
    try:
        del pbp_tracker[command.channel.id]
        try:
            pending_deletion = []
            async for msg in client.logs_from(command.channel):
                if msg.content.startswith(mstr.PBP_WAITING):
                    pending_deletion.append(msg)
            for m in pending_deletion:
                await client.delete_message(m)
        except Exception as e:
            print('Failed to delete old "Waiting for" messages')
            print(e)
        save_pbp()
        return mstr.PBP_STOPPED
    except KeyError:
        return mstr.PBP_STILL_STOPPED

@bot.command()
async def wiki(command) -> '<Page Title>':
    '''Searches for and grabs a link to the page of the given title from the following wiki sites: {wiki}'''
    if command.args:
        w = 0
        term = ' '.join(command.args)
        print(f'retrieve "{term}" from wikia...')

        for sub in config.get(command.server.id, 'wikia_list').split(','):
            try:
                w = wikia.page(sub.strip(' []'), term)
                print('page found on {0}...'.format(sub))
                break #page found, exit the for loop
            except:
                w = 0
                print(f'page not found in {sub}')
        
        if w is not 0:
            return w.url.replace(' ','_')
        else:
            return f':sweat: Sorry, I couldnt find a page titled "{term}"...'
    else:
        print('no search term...')
        return 'Use **!wiki <Page Title>** to search and grab a link to the page of that title on the following wiki sites: {}'.format(config.get(command.server.id, 'wikia_list'))

#endregion !SECTION

@client.event
async def on_message(message):
#SECTION COMMAND LOGIC
    #Ignore own messages
    if message.author == client.user:
        return

    #NOTE MAGICALLY PROCESS COMMANDS
    try:
        cmd = CommandPacket(message)
        msg = await bot.do(cmd)
    except CommandError: 
        pass #Raised if string is not a command
    else:
        await client.send_message(cmd.channel, msg)
        return
#!SECTION 

#SECTION GENERAL MESSAGE LOGIC
    #ANCHOR CHANNEL LINKING
    try:
        if message.author.id in links[message.server.id][message.channel.id]:
            for channel in links[message.server.id][message.channel.id][message.author.id]:
                embedable = discord.Embed(description = message.content)#, timestamp = message.timestamp)
                embedable.set_footer(text = 'from #' + message.channel.name)
                embedable.set_author(name= message.author.name, icon_url= message.author.avatar_url if not message.author.avatar_url == '' else message.author.default_avatar_url)
                await client.send_message(client.get_channel(channel), embed = embedable)
        elif 'all' in links[message.server.id][message.channel.id]:
            for channel in links[message.server.id][message.channel.id]['all']:
                embedable = discord.Embed(description = message.content)#, timestamp = message.timestamp)
                embedable.set_author(name= message.author.name, icon_url= message.author.avatar_url if message.author.avatar_url != '' else message.author.default_avatar_url)
                await client.send_message(client.get_channel(channel), embed = embedable)
                break
    except KeyError: #Raised when Server or Channel is not in Links
        pass

    #ANCHOR PBP Tracking
        if await check_pbp(message):
            return #Stop message processing

    #ANCHOR RULE REFERENCE
    for book in books.keys():
        terms = re.findall(r'{0}\s(?:p|pg)?\s?(\d+)'.format(book), message.content, re.IGNORECASE)
        if terms:
            print(f'Detected reference command: {book}')
            print(f'{len(terms)} {book} terms found!')
            string = ""
            for t in terms:
                print('PAGE ' + t)
                z = ''
                u = int(t) + int(books[book]['offset'])
                if int(u) < 10:
                    z = '0'
                page_number = z + str(u)
                string = string + book + ' ' + t + ': ' + books[book]['url'].format(page=page_number) + '\n'
            await client.send_message(message.channel, string)
#!SECTION

async def check_pbp(message):
    #PBP Structure
    #{channel.id:[{group1}, {group2), ]}
    #group -> {member_id:bool, }
    if message.channel.id in pbp_tracker:
        channel = message.channel
        instance = pbp_tracker[channel.id]
        author = message.author.id
        members_left = []
        for group in instance:
            for member in group.keys():
                if member == author:
                    group[member] = True
                if not group[member]:
                    members_left.append(member)
            if members_left:
                break
        #if the round is over, refresh the list
        if not members_left:
            for group in instance:
                for member in group.keys():
                    group[member] = False
            for group in instance:
                for member in group.keys():
                    if not group[member]:
                        members_left.append(member)
                if members_left:
                    break
        pbp_tracker[channel.id] = instance

        try:
            pending_deletion = []
            async for msg in client.logs_from(channel):
                if msg.content.startswith(mstr.PBP_WAITING):
                    pending_deletion.append(msg)
            for msg in pending_deletion:
                await client.delete_message(msg)
        except Exception as e:
            print('Failed to delete old "Waiting for" messages')
            print(e)

        string = mstr.PBP_WAITING + '\n'
        for m in members_left:
            string = string + f'<@!{m}>\t'
        await client.send_message(channel, string)
        save_pbp()
        return True #ignore rule reference triggers
    else:
        return False

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

#ANCHOR GetMembersFromRole
def getMembersFromRole(server, role):
    '''Return a list of member ids that are part of the given role name or id'''
    role = role.replace('<','').replace('>','').replace(' ','')
    members = []
    if role.startswith('&'):
        #is a role id
        role = role.replace('&','')
        for member in server.members:
            for s_role in member.roles: 
                if s_role.id == role:
                    members.append(member.id)
                    break
        return members
    elif role.startswith('@'):
        #is a role name
        role = role.replace('@','')
        for member in server.members:
            for s_role in member.roles: 
                if s_role.name == role:
                    members.append(member.id)
                    break
        return members
    elif re.search(r'\d+', role):
        #numerical id given
        for member in server.members:
            for s_role in member.roles: 
                if s_role.id == role:
                    members.append(member.id)
                    break
        return members
    else:
        #invalid role
        del members
        raise TypeError('Cannot get Members from Role, Role must be ID or Name string')

#SECTION UPTIME FUNCTIONS
#ANCHOR UPTIME
def get_uptime():
    time_now = datetime.datetime.utcnow()
    time_delta = time_now - time_start
    uptime_string = 'Reverb has been running for {0} Days, {1} Hours, {2} Minutes, and {3} Seconds'.format(str(time_delta.days), str(time_delta.seconds//3600), str((time_delta.seconds//60)%60), str(time_delta.seconds%60))
    return uptime_string
#ANCHOR SYSUPTIME
def get_sysuptime():
    sysuptime_seconds = int(UptimeModule.uptime())
    sysuptime_delta = datetime.timedelta(seconds = sysuptime_seconds)
    sysuptime_string = 'OS has been running for {0} Days, {1} Hours, {2} Minutes, and {3} Seconds'.format(str(sysuptime_delta.days), str(sysuptime_delta.seconds//3600), str((sysuptime_delta.seconds//60)%60), str(sysuptime_delta.seconds%60))
    return sysuptime_string
#!SECTION

#SECTION PLAY BY POST MANAGEMENT FUNCTIONS
#ANCHOR SAVE PBP TRACKER
def save_pbp():
    with open('pbp.json', 'w') as outfile:
        json.dump(pbp_tracker, outfile)
    return
#!SECTION

#SECTION CHANNEL LINK MANAGEMENT FUNCTIONS
#ANCHOR SAVE CONFIG
def save_links():
    with open('links.json', 'w') as outfile:
        json.dump(links, outfile)
    print('links saved')
    return
#ANCHOR ADD LINK
def add_link(server,channel_src,user,channel_dest):
    '''Adds a chat-mirror link to the links file.'''
    try:
        if server not in links: links.update({server : {}})
        if channel_src not in links[server]: links[server].update({channel_src : {}})
        if user not in links[server][channel_src]: links[server][channel_src].update({user : []})

        if channel_dest not in links[server][channel_src][user]:
            links[server][channel_src][user].append(channel_dest)
            save_links()
            return mstr.UPDATE_SUCCESS
        else:
            return mstr.UPDATE_DUPLICATE
    except:
        return mstr.UPDATE_ERROR
#ANCHOR REMOVE LINK
def remove_link(server,channel_src,user,channel_dest):
    '''Removes a chat-mirror link in the links file.'''
    try:
        if channel_dest in links[server][channel_src][user]:
            links[server][channel_src][user].remove(channel_dest)
            save_links()
            return mstr.UPDATE_SUCCESS
        else:
            return mstr.UPDATE_NOT_FOUND
    except:
        return mstr.UPDATE_ERROR
#!SECTION

#NOTE Create and set Ledger instances
karma = Ledger('karma','Karma')
nuyen = Ledger('nuyen', '¥', 'prefix')
edge = Ledger('edge', 'Edge')

#STARTUP CONNECTION ON_READY
@client.event
async def on_ready():
    await client.change_presence(game=discord.Game(name='"!reverb help" for help'))
    print('We have logged in as {0.user}'.format(client))

# !reverb @USERNAME#0000 to #CHANNEL_DEST

# @client.event
# async def on_message(message):
#     #ignore all messages sent by self
#     if message.author == client.user:
#         return

#     #NOTE Reset per-message flags
#     pbp_ignore = False

# #SECTION !COMMANDS
#     if message.content.startswith(COMMAND_CHAR):
#         #NOTE Get author info and print
#         try:
#             command(message)
#         except:
#             pass

#         #this message does not count as a post for the member for pbp tracking
#         pbp_ignore = True 



#         #check permissions and store in vars
#         isAdmin = message.author.server_permissions.administrator
#         isGM = False
#         isPlayer = False

#         for r in message.author.roles:
#             if r.name.startswith('gm'): isGM = True
#             if r.name.startswith('players'): isPlayer = True
#             if r.name.startswith('player'): isPlayer = True

#         #print author in console and respond to commands
#         print(str(message.author) + ' <@{}>'.format(message.author.id))
#         print('Role(s): {0}{1}{2}'.format('Admin ' if isAdmin else '', 'GM ' if isGM else '', 'Player ' if isPlayer else ''))
#         print(message.content)

#     #trigger commands with "!reverb" keyword
#     if message.content.startswith('!reverb'):

#         #return out if not admin, send refusal message
#         if not isAdmin:
#             print('refused command: {0}'.format(message.content))
#             print('CommandObject requires Server Admin')
#             return
# #ANCHOR REVERB HELP
#         if message.content.startswith('!reverb help'):
#             with open('help.md','r') as h:
#                 await client.send_message(message.channel, h.read())
#             print('sent help text')
#             return
# #ANCHOR REVERB UNLINK @USER #CHANNEL
#         elif message.content.startswith("!reverb unlink"):
#             terms = re.search(r"!reverb unlink <@(.+)> <#(.+)>", message.content)
#             if terms:
#                 print(terms.group(1))
#                 print(terms.group(2))
#                 print('remove forward: #{0} from <@{1}> to <#{2}>'.format(message.channel.name, terms.group(1), terms.group(2)))
                
#                 s = remove_link(message.server.id,message.channel.id,terms.group(1),terms.group(2))
#                 if s is UPDATE_SUCCESS:
#                     await client.send_message(message.channel, '{0} No longer forwarding messages in <#{1}> from <@{2}> to <#{3}>'.format(s, message.channel.id, terms.group(1), terms.group(2)))
#                 else:
#                     await client.send_message(message.channel, s)
#                 return
#             else:
#                 print('Invalid channel in command: {0}'.format(message.content))
#                 return
#         global clear_flag
# #ANCHOR REVERB CLEAR ALL
#         if message.content.startswith('!reverb clear all'):
            
#             if message.author.id not in clear_flag:
#                 clear_flag.append(message.author.id)
#                 await client.send_message(message.channel, content = 'Are you sure you wish to clear all link data for this server? __This cannot be undone!__ Send "**!reverb clear all**" again to proceed.')
#             else:
#                 clear_flag.remove(message.author.id)
#                 links[message.server.id] = {}
#                 save_links()
#                 await client.send_message(message.channel, content = 'All active links on this server have been removed.')
#                 print('server links cleared')
#             return
#         else:
#             if message.author.id in clear_flag: clear_flag.remove(message.author.id)

#         #iterate down command list until a matching command is found
# #ANCHOR REVERB PING
#         if message.content.startswith('!reverb ping'):
#             await client.send_message(message.channel, content = "Pong!")
#             print(message.author)
#             return
# #ANCHOR REVERB RESTART
#         elif message.content.startswith('!reverb restart'):
#             print('*********Restarting script...**********')
#             os._exit(1)
#             #restart script code
#             return









#     #message does not contain !reverb keyword, iterate through other commands
# #ANCHOR KARMA HISTORY
#     elif message.content.startswith('!karma history'):
#         if isGM:
#             terms = re.search(r'!karma history <@([\d,!]+)>\s?(\d+)?', message.content)
#             if terms:
#                 server = message.server.id
#                 user = terms.group(1)
#                 try:
#                     lines = int(terms.group(2))
#                 except:
#                     lines = 5
#                 history = karma.gethistory(server, user, lines)
#                 msg = 'Here are the last {0} entries for <@{1}>: ```{2}```'.format(lines, user, history)
#                 await client.send_message(message.channel, msg)
#                 return
#             else:
#                 await client.send_message(message.channel, 'You must use a proper \'@\' reference to look up player Karma history')
#                 return
#         if isPlayer:
#             terms = re.search(r'!karma history (\d+)', message.content)
#             try:
#                 lines = int(terms.group(1))
#             except:
#                 lines = 5
#             server = message.server.id
#             user = message.author.id
#             history = karma.gethistory(server, user, lines)
#             msg = 'Here are the last {0} entries for <@{1}>: ```{2}```'.format(lines, user, history)
#             await client.send_message(message.channel, msg)
#             return
# #ANCHOR KARMA
#     elif message.content.startswith('!karma'):
#         if isGM:
#             terms = re.search(r'!karma (-?\d+) ((?:<?@[\d,\w,!,&]+>?\s?)+)\s?([\w,\s]+)?', message.content)
#             if terms:
#                 server = message.server.id
#                 diff = terms.group(1)
#                 players = terms.group(2)
#                 if players.startswith('@player'):
#                     players = []
#                     for member in message.server.members:
#                         for role in member.roles: 
#                             if role.name.startswith('player'):
#                                 players.append(member.id)
#                                 break
#                     if not players:
#                         await client.send_message(message.channel, 'It looks like the role \'{}\' has no members'.format(terms.group(2)))
#                         return
#                 elif re.search('.*&.*', players):
#                     role_id = re.search(r'.*<@&(\d+)>.*', terms.group(2)).group(1)
#                     players = []
#                     for member in message.server.members:
#                         for role in member.roles: 
#                             if role.id.startswith(role_id):
#                                 players.append(member.id)
#                                 break
#                     if not players:
#                         await client.send_message(message.channel, 'It looks like the role \'{}\' has no members'.format(terms.group(2)))
#                         return
#                 else:
#                     players = terms.group(2).replace('<@','').replace('!','').replace('>','').split(' ')
#                     players = list(filter(None, players))
#                 if not terms.group(3):
#                     await client.send_message(message.channel, 'All Karma transactions must have a reason noted. (i.e. `!karma <#> <@recipient(s)> <reason>`)')
#                     return
#                 else:
#                     note = terms.group(3)
#                 msg = '**{} Karma** has been added to '.format(diff) if int(diff) > 0 else '**{} Karma** has been spent by '.format(abs(int(diff)))
#                 for player in players:
#                     karma.addentry(server, player, diff, note)
#                     msg = '{0}<@{1}> '.format(msg, player)
#                 karma.savetofile()
#                 msg = '{0}for \"{1}\"'.format(msg, note)
#                 await client.send_message(message.channel, msg)
#                 return
#             else:
#                 terms = re.search(r'!karma ((?:<@[\d,!]+>\s?)+)', message.content)
#                 if terms:
#                     server = message.server.id
#                     players = filter(None, terms.group(1).replace('<@','').replace('!','').replace('>','').split(' '))
#                     for player in players:
#                         await client.send_message(message.channel, '<@{0}> currently has **{1}**'.format(player, karma.getbalance(server, player)))
#                 else:
#                     await client.send_message(message.channel, 'The GM has **all the Karma**')
#                 return
#         elif isPlayer:
#             server = message.server.id
#             player = message.author.id
#             await client.send_message(message.channel, '<@{0}>, you currently have {1}'.format(message.author.id, karma.getbalance(server, player)))
#             return
# #ANCHOR CASH HISTORY
#     elif message.content.startswith('!cash history'):
#         if isGM:
#             terms = re.search(r'!cash history <@([\d,!]+)>\s?(\d+)?', message.content)
#             if terms:
#                 server = message.server.id
#                 user = terms.group(1).replace('!','')
#                 try:
#                     lines = int(terms.group(2))
#                 except:
#                     lines = 5
#                 history = nuyen.gethistory(server, user, lines)
#                 msg = 'Here are the last {0} entries for <@{1}>: ```{2}```'.format(lines, user, history)
#                 await client.send_message(message.channel, msg)
#                 return
#             else:
#                 await client.send_message(message.channel, 'You must use a proper \'@\' reference to look up player cash history')
#                 return
#         if isPlayer:
#             terms = re.search(r'!cash history (\d+)', message.content)
#             try:
#                 lines = int(terms.group(1))
#             except:
#                 lines = 5
#             server = message.server.id
#             user = message.author.id
#             history = nuyen.gethistory(server, user, lines)
#             msg = 'Here are the last {0} entries for <@{1}>: ```{2}```'.format(lines, user, history)
#             await client.send_message(message.channel, msg)
#             return
# #ANCHOR CASH
#     elif message.content.startswith('!cash'):
#         if isGM:
#             terms = re.search(r'!cash (-?\d+) ((?:<?@[\d,\w,!]+>?\s?)+)\s?([\w,\s]+)?', message.content)
#             if terms:
#                 server = message.server.id
#                 diff = terms.group(1)
#                 if terms.group(2).startswith('@player'):
#                     players = []
#                     for member in message.server.members:
#                         for role in member.roles: 
#                             if role.name.startswith('player'):
#                                 players.append(member.id)
#                                 break
#                     if not players:
#                         await client.send_message(message.channel, 'It looks like the role \'{}\' has no members'.format(terms.group(2)))
#                         return
#                 else:
#                     players = terms.group(2).replace('<@','').replace('!','').replace('>','').split(' ')
#                     players = list(filter(None, players))
#                 if not terms.group(3):
#                     await client.send_message(message.channel, 'All cash transactions must have a reason noted. (i.e. `!cash <amount> <@recipient> <reason>`)')
#                     return
#                 else:
#                     note = terms.group(3)
#                 msg = '**¥{}** has been given to '.format(diff) if int(diff) > 0 else '**¥{}** has been spent by '.format(abs(int(diff)))
#                 for player in players:
#                     nuyen.addentry(server, player, diff, note)
#                     msg = '{0}<@{1}> '.format(msg, player)
#                 nuyen.savetofile()
#                 msg = '{0}for \"{1}\"'.format(msg, note)
#                 await client.send_message(message.channel, msg)
#                 return
#             else:
#                 terms = re.search(r'!cash ((?:<@[\d,!]+>\s?)+)', message.content)
#                 if terms:
#                     server = message.server.id
#                     players = terms.group(1).replace('<@','').replace('!','').replace('>','').split(' ')
#                     print('Get balance for: {}'.format(str(players)))
#                     for player in players:
#                         await client.send_message(message.channel, '<@{0}> currently has **{1}**'.format(player, nuyen.getbalance(server, player)))
#                 else:
#                     await client.send_message(message.channel, 'Could not find an @ reference in your request...')
#                 return
#         elif isPlayer:
#             terms = re.search(r'!cash (\d+) ((?:<?@[\d,\w,!]+>?\s?)+)\s?([\w,\s]+)?', message.content)
#             server = message.server.id
#             sender = message.author.id
#             if not terms:
#                 await client.send_message(message.channel, '<@{0}>, you currently have {1}'.format(sender, nuyen.getbalance(server, sender)))
#                 return
#             if terms:
#                 diff = terms.group(1)
#                 if not terms.group(2):
#                     await client.send_message(message.channel, 'You must specify a recipient!')
#                     return
#                 recipient = terms.group(2).replace('<@','').replace('!','').replace('>','').replace(' ','')
#                 member = message.server.get_member(recipient)
#                 s_nick = message.author.display_name
#                 r_nick = member.display_name
#                 note = 'Sent to {}'.format(r_nick)
#                 if terms.group(3):
#                     note = note + ' - ' + terms.group(3)
#                 nuyen.addentry(server, sender, -int(diff), note)
#                 note = note.replace('Sent to {}'.format(r_nick), 'Recieved from {}'.format(s_nick))
#                 nuyen.addentry(server, recipient, diff, note)
#                 nuyen.savetofile()
#                 await client.send_message(message.channel, 'Succesfully transferred {0}{1} from <@{2}> to <@{3}>'.format(nuyen.unit_string, diff, sender, recipient))
#                 return
#             terms = re.search(r'!cash (-?\d+) ((?:[\w,\s]+))', message.content)
#             if terms:
#                 return
# #ANCHOR WIKI
#     elif message.content.startswith('!wiki'):
#         
# #!SECTION
#     else:


    # await test_bot.process_commands(message)
client.run(bot_token)
# test_bot.run(bot_token)
