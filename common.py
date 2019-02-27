import discord
import asyncio
import re
import json
from datetime import datetime
import message_strings as mstr

#ANCHOR Save Config
def save_config(config, fn, *header):
    with open(fn, 'w+') as f:
        for l in header:
            f.write(l + '\n')
        else:
            f.write('\n')
        config.write(f)

#ANCHOR Read JSON File
def read_json_file(filename, default = dict()):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filename, 'w+') as f:
            json.dump(default, f, indent=4)
            return default

#ANCHOR Save JSON
def save_json_file(obj, fn):
    with open(fn, 'w+'):
        json.dump(obj, fn, indent=4)

#ANCHOR Delete Messages
async def deleteMessages(client, msg_list):
    for msg in msg_list:
        await client.delete_message(msg)
        await asyncio.sleep(1.2)

#ANCHOR Get Members from Role
def get_members_from_role(guild, role):
    '''Return a list of member ids that are part of the given role name or id'''
    role = role.strip('<> \t\n\r')
    members = []
    if role.startswith('@'):
        #is a role name
        role = role.replace('@','')
        for member in guild.members:
            for s_role in member.roles: 
                if s_role.name == role:
                    members.append(member.id)
                    break
        return members
    elif re.search(r'&?\d+', role):
        #numerical id given
        role = role.replace('&','')
        for member in guild.members:
            for s_role in member.roles: 
                if s_role.id == role:
                    members.append(member.id)
                    break
        return members
    else:
        #invalid role
        del members
        raise TypeError('Role must be ID or Name string')

#SECTION PLAY BY POST MANAGEMENT FUNCTIONS
#ANCHOR SAVE PBP TRACKER
def save_pbp(pbp_tracker):
    with open('pbp.json', 'w') as outfile:
        json.dump(pbp_tracker, outfile)
    return
#!SECTION

#SECTION CHANNEL LINK MANAGEMENT FUNCTIONS
#ANCHOR SAVE CONFIG
def save_links(links):
    with open('links.json', 'w') as outfile:
        json.dump(links, outfile)
    print('links saved')
    return

#ANCHOR ADD LINK
def add_link(links, guild, channel_src, user, channel_dest):
    '''Adds a chat-mirror link to the links file.'''
    try:
        if guild not in links: links.update({guild : {}})
        if channel_src not in links[guild]: links[guild].update({channel_src : {}})
        if user not in links[guild][channel_src]: links[guild][channel_src].update({user : []})

        entry = links[guild][channel_src][user]

        if channel_dest not in entry:
            entry.append(channel_dest)
            links.save()
            return mstr.UPDATE_SUCCESS
        else:
            return mstr.UPDATE_DUPLICATE
    except:
        return mstr.UPDATE_ERROR

#ANCHOR REMOVE LINK
def remove_link(links, guild,channel_src,user,channel_dest):
    '''Removes a chat-mirror link in the links file.'''
    try:
        if channel_dest in links[guild][channel_src][user]:
            links[guild][channel_src][user].remove(channel_dest)
            links.save()
            return mstr.UPDATE_SUCCESS
        else:
            return mstr.UPDATE_NOT_FOUND
    except:
        return mstr.UPDATE_ERROR
#!SECTION