import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
from discord.ext import commands
import json
import logging
import re
import discord

'''Catch and link to rulebook references'''

log = logging.getLogger('bot.' + __name__)

class Reference(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_books()
    def load_books(self):
        with open(os.path.join(parentdir, "data", "reference_books.json"), 'r') as f:
            self.books = json.load(f)
    def save_books(self):
        json.dump(self.books, os.path.join(self.books, parentdir, "data", "reference_books.json"), indent=4)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user \
        or message.content.startswith(self.bot.command_prefix):
            return
        for book in self.books.keys():
            terms = re.findall(r'{0}\s(?:p|pg|page)?\s?(\d+)'.format(book), message.content, re.IGNORECASE)
        if terms:
            log.debug(f'Detected reference command: {book}')
            log.debug(f'{len(terms)} {book} terms found!')
            string = ""
            for t in terms:
                log.debug('PAGE ' + t)
                z = ''
                u = int(t) + int(self.books[book].get('offset'))
                if int(u) < 10:
                    z = '0'
                page_number = z + str(u)
                string = string + book + ' ' + t + ': ' + self.books[book]['url'].format(page=page_number) + '\n'
            await message.channel.send(string)

def setup(bot):
    bot.add_cog(Reference(bot))
    log.info('Loaded!')