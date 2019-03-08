import discord
from JsonFileObject import JsonFileObject
from discord.ext import commands
import logging

log = logging.getLogger('bot.' + __name__)

class GameCommands:

    def __init__(self, bot):

        self.bot = bot
        self.npcs = JsonFileObject('npcs.json')

    @commands.command()
    async def open(self, ctx):
        await ctx.message.delete()
        player = [x for x in ctx.guild.roles if x.name.lower().startswith('player')]
        await ctx.channel.set_permissions(player[0], send_messages = True)
        await ctx.send('```This log is now open for player entries```')

    @commands.command()
    async def close(self, ctx):
        await ctx.message.delete()
        await ctx.send('```This log is closed, The next chapter will open soon```')
        await ctx.channel.edit(sync_permissions = True)

    @commands.command()
    async def mimic(self, ctx, user, *, message):
        await ctx.message.delete()

        person = {}

        if user.startswith('<'):
            m = ctx.guild.get_member(int(user.strip('<!@>')))
            avatar = m.avatar_urlif if not m.avatar_url else m.default_avatar_url
            person.update({'name': m.name, 'avatar_url': avatar})
            log.debug(f'{ctx.author.name} is impersonating {user}, {m.name}')
        else:
            npc_list = self.npcs.get(str(ctx.guild.id))
            if user in npc_list:
                npc = npc_list.get(user)
                person.update({'name': npc['display_name'], 'avatar_url': npc['avatar_url']})
                log.debug(f'{ctx.author.name} is impersonating NPC, {npc["display_name"]}')

        if person:
            embedable = discord.Embed(description = message)#, timestamp = ctx.timestamp)
            #embedable.set_footer(text = 'sent by GM')
            embedable.set_author(name= person['name'])#, icon_url= person['avatar_url'])
            embedable.set_thumbnail(url = npc['avatar_url'])
            await ctx.send(embed = embedable)

    @commands.command()
    async def addnpc(self, ctx, name, display_name, avatar_url):
        await ctx.message.delete()

        npc_list = self.npcs.get(str(ctx.guild.id))
        if npc_list:
            npc_list.update({name:{'display_name': display_name, 'avatar_url': avatar_url}})
            self.npcs.save()
        else:
            self.npcs.update({str(ctx.guild.id):{name:{'display_name': display_name, 'avatar_url': avatar_url}}})
            self.npcs.save()
        
        npc = self.npcs[str(ctx.guild.id)][name]

        log.debug(npc)

        embedable = discord.Embed(description = f'NPC profile has been saved to {ctx.guild.name}. Make sure everything looks as you expect it to here :smile:')#, timestamp = ctx.message.timestamp)
        embedable.set_footer(text = f'!mimic "{name}"')
        embedable.set_author(name= npc.get('display_name'), icon_url= npc.get('avatar_url'))

        log.debug(f'Embedded npc example: {embedable}')

        await ctx.author.send(embed = embedable)

def setup(bot):
    bot.add_cog(GameCommands(bot))
    log.info('Loaded!')