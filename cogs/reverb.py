import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import discord
from discord.ext import commands
from common.classes import JsonFileObject
import message_strings as mstr
import logging
import common

log = logging.getLogger('bot.' + __name__)

class Reverb:

    def __init__(self, bot):

        self.bot = bot
        self.links = JsonFileObject('links.json')

    async def on_message(self, message):

        if message.author == self.bot.user or message.content.startswith(self.bot.command_prefix):
            return

        guild = str(message.guild.id)
        ch_src = str(message.channel.id)
        author = str(message.author.id)

        log.info('Checking for links...')
        log.info(f'Author: {author}')
        
        try:
            table = self.links[guild]
        except KeyError:
            logging.debug(f'Guild not in links: {message.guild.name}')
            return
        
        embedable = discord.Embed(description = message.content)#, timestamp = ctx.timestamp)
        embedable.set_footer(text = 'from #' + message.channel.name)
        embedable.set_author(name= message.author.name, icon_url= message.author.avatar_url if not message.author.avatar_url == '' else message.author.default_avatar_url)
        
        channels = []

        try:
            for channel in table[ch_src]['all']:
                if channel not in channels:
                    channels.append(channel)
        except KeyError:
            pass

        try:
            for channel in table[ch_src][author]:
                if channel not in channels:
                    channels.append(channel)
        except KeyError:
            pass

        for channel in channels:
            await self.bot.get_channel(int(channel)).send(embed = embedable)

    @commands.command()
    @commands.has_permissions(administrator = True)  
    async def unlink(self, ctx, user, channel_dest):
        '''Removes a chat-mirror link.'''

        user = user.strip('<@!>')
        channel_src = str(ctx.channel.id)
        guild = str(ctx.guild.id)

        try:
            self.links[guild][channel_src][user].remove(channel_dest)
            self.links.save()
            await ctx.send(mstr.UPDATE_SUCCESS)
        except (KeyError, ValueError):
            await ctx.send(mstr.UPDATE_NOT_FOUND)
        except:
            await ctx.send(mstr.UPDATE_ERROR)

    def get_links(self):

        pass

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def link(self, ctx, user, channel_dest):
        '''Copy messages from @tag in this channel to #destination channel. \'all\' may be used to echo all messages'''
        guild = str(ctx.guild.id)
        ch_src = str(ctx.channel.id)
        ch_dest = channel_dest.strip('<#>')
        author = str(ctx.author.id)

        if guild not in self.links:
            self.links.update({guild: {'__name__': ctx.guild.name, ch_src:{author: [ch_dest]}}})
            await ctx.send(mstr.UPDATE_SUCCESS)
            self.links.save()
            return
        elif ch_src not in self.links[guild]:
            self.links[guild].update({ch_src:{author:ch_dest}})
            await ctx.send(mstr.UPDATE_SUCCESS)
            self.links.save()
            return
        elif author not in self.links[guild][ch_src]:
            self.links[guild][ch_src].update({author:[ch_dest]})
            await ctx.send(mstr.UPDATE_SUCCESS)
            self.links.save()
            return
        else:
            if ch_dest in self.links[guild][ch_src][author]:
                await ctx.send(mstr.UPDATE_DUPLICATE)
                return
            self.links[guild][ch_src][author].append(ch_dest)
            self.links.save()
            await ctx.send(mstr.UPDATE_SUCCESS)

def setup(bot):
    bot.add_cog(Reverb(bot))
    log.info('Loaded!')