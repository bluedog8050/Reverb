from discord.ext import commands

'''Basic Debug utilities to make sure I am doing things right'''

class Debug():
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def ping(self, ctx):
        '''Ping for response'''
        await ctx.send('Pong!')
    @commands.command()
    async def echo(self, ctx, *, message):
        '''Echo a declared string'''
        await ctx.send(message)

def setup(bot):
    try:
        bot.add_cog(Debug(bot))
        print('Debug extension loaded!')
    except:
        print('Unable to load Debug extension!')
        raise