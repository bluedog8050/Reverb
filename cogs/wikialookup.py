import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import wikia as wikia_module
from common.classes import JsonFileObject
import logging
from discord.ext import commands
'''Basic Debug utilities to make sure I am doing things right'''

log = logging.getLogger('bot.' + __name__)


class WikiaLookup():

    def __init__(self, bot):
        self.bot = bot
        self.wikia_list = JsonFileObject('wikia.json')

    @commands.command()
    async def wikia(self, ctx, *, term=''):
        '''Searches for and grabs a link to the page of the given title from the set wiki sites.'''

        if not self.wikia_list.get(str(ctx.guild.id)):
            await ctx.send(f'No wikias have been set for this guild. Use the `{self.bot.command_prefix}wikialist` command to add some to the list')
            return
        if term:
            async with ctx.channel.typing():
                w = 0
                log.info(f'retrieve "{term}" from wikia...')

                for sub in self.wikia_list.get(str(ctx.guild.id)):
                    try:
                        w = wikia_module.page(sub.strip(' []'), term)
                        log.info('page found on {0}...'.format(sub))
                        break  # page found, exit the for loop
                    except:
                        w = 0
                        log.info(f'page not found in {sub}')

                if w is not 0:
                    await ctx.send(w.url.replace(' ', '_'))
                else:
                    await ctx.send(f':sweat: Sorry, I couldnt find a page titled "{term}"...')
        else:
            log.info('no search term...')
            await ctx.send('Use **!wiki <Page Title>** to search and grab a link to the page of that title on the following wiki sites: {}'.format(self.wikia_list[ctx.guild.id]))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wikialist(self, ctx, *, wikias=''):
        '''Set the list of wikias that will be searched using the !wikia command. List wikias in a space separated list'''
        if wikias:
            self.wikia_list.update({str(ctx.guild.id): wikias.split(' ')})
            self.wikia_list.save()
            await ctx.send(f'Wikia list updated! :thumbsup: ```{self.wikia_list[str(ctx.guild.id)]}```')
        else:
            await ctx.send(f'The following wikias are searched in order until a match is found: ```{self.wikia_list[str(ctx.guild.id)]}```')


def setup(bot):
    bot.add_cog(WikiaLookup(bot))
    log.info('Loaded!')
