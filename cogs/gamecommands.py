from discord.ext import commands
import logging

log = logging.getLogger(__name__)

gm_roles = ['reverb-gm', 'gm','game master', 'dm', 'dungeon master', 'GM','Game Master', 'DM', 'Dungeon Master']
player_roles = ['reverb-player', 'player', 'players']

class GameCommands:
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    @commands.has_any_role(gm_roles)
    async def open(self, ctx):
        pass
    @commands.command()
    @commands.has_any_role(gm_roles)
    async def close(self, ctx):
        pass

def setup(bot):
    bot.add_cog(GameCommands(bot))
    log.info('Loaded!')