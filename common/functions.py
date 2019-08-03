import discord

def get_member_name(id : str, guild : discord.Guild):
    if id.startswith('<@'): id = id.strip("<@!>")

    member = guild.get_member(id)

    return member.nick or member.name