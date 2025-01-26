import discord
from discord.ext import commands
import asyncio
from config import settings
from discord.ext.commands import errors
from model.dbc_model import Player, Game
from common.database_connection import tournament_dbc
from model.dbc_model import Game, Player

'''
we use bot.start(): 
    to start bot asynchroneousely
    we have a chnace to customize event loop to increase the perfomance
    flexiablity because of we can set up custom logic or tasks before or after the botstarts running
'''

logger = settings.logging.getLogger("discord")

async def main():
    logger.info("start bot")

    intents = discord.Intents.default()
    intents.members = True  # Make sure to enable the intent to access members' information.
    intents.message_content = True

    bot = commands.Bot(command_prefix="$", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"loged into server as {bot.user}")

        # Load the cogs (controllers)
        await bot.load_extension('controller.players_detail')
        await bot.load_extension('controller.giveaway_cog')

        guild = bot.get_guild(settings.GUILD_ID)

        #copy the global slash commands to the specific guild
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)

    
    # Initialize the database and create tables
    tournament_dbc.connect()
    tournament_dbc.create_tables([Game, Player])

    #error handling
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, errors.ArgumentParsingError):
            await ctx.send("there is parsing error")
        if isinstance(error, errors.CommandNotFound):
            await ctx.send("Invalid command from global error handler")
        elif isinstance(error, errors.MissingRequiredArgument):
            await ctx.send("Please pass the required arguments from global error handler")
        elif isinstance(error, errors.BadArgument):
            await ctx.send("Please pass the correct arguments from global error handler")
        elif isinstance(error, errors.CommandOnCooldown):
            await ctx.send("This command is on cooldown, please try again later from global error handler")
        else:
            await ctx.send("Something went wrong, from global error handler")
    
    # Run the bot with your token
    await bot.start(settings.DISCORD_API_SECRET, reconnect=True)

if __name__ == "__main__":
    asyncio.run(main())