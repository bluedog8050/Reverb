import discord
import asyncio
import re
import json

def saveConfig(config, fn, *header):
    with open(fn, 'w+') as f:
        for l in header:
            f.write(l + '\n')
        f.write('\n')
        config.write(f)

async def deleteMessages(client, msg_list):
    for msg in msg_list:
        await client.delete_message(msg)
        await asyncio.sleep(1.2)

def readJsonFile(filename, default = dict()):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filename, 'w+') as f:
            json.dump(default, f)
            return default

def saveJsonFile(obj, fn):
    with open(fn, 'w+'):
        json.dump(obj, fn)

def getMembersFromRole(server, role):
    '''Return a list of member ids that are part of the given role name or id'''
    role = role.strip('<> \t\n\r')
    members = []
    if role.startswith('@'):
        #is a role name
        role = role.replace('@','')
        for member in server.members:
            for s_role in member.roles: 
                if s_role.name == role:
                    members.append(member.id)
                    break
        return members
    elif re.search(r'&?\d+', role):
        #numerical id given
        role = role.replace('&','')
        for member in server.members:
            for s_role in member.roles: 
                if s_role.id == role:
                    members.append(member.id)
                    break
        return members
    else:
        #invalid role
        del members
        raise TypeError('Role must be ID or Name string')
