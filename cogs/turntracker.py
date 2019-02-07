from discord.ext import commands

class Tracker:
    def __init__(self, bot):
        self.bot = bot
    async def on_message(self, ctx):
        print('message received')

def setup(bot):
    bot.add_cog(Tracker(bot))
    print('Turn Tracker extension loaded!')