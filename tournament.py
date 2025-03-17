import discord
from discord.ext import commands
import asyncio
from config import settings
from discord.ext.commands import errors
from model.dbc_model import Tournament_DB, Player, Player_game_info
from common.cached_details import Details_Cached


'''
we use bot.start(): 
    to start bot asynchronously
'''

logger = settings.logging.getLogger("discord")

async def main():
    logger.info("Start Bot")

    intents = discord.Intents.default()
    intents.members = True 
    intents.message_content = True

    sys_client = commands.Bot(command_prefix="$", intents=intents)

    # Initialize the database and create tables
    db = Tournament_DB()
    Player.createTable(db)
    Player_game_info.createTable(db)


    @sys_client.event
    async def on_ready():
        logger.info(f"Logged into server as: {sys_client.user}")

        #create a channels and save cached created channels on all server bot is running
        for guild in sys_client.guilds:
            logger.info(f"the guild value is: {guild.id}")
            await Details_Cached.channels_for_tournament(ch_config=settings.CHANNEL_CONFIG, guild=guild)

        # Load the cogs (controllers)
        for cmd_file in settings.controller_dir.glob("*.py"):
            if cmd_file.name != "__init__.py" and cmd_file.name != "signup_shared_logic.py" and cmd_file.name != "match_making.py" and cmd_file.name != "openAi_teamup.py" and cmd_file.name != "tournamentBracket.py":
                try:
                    await sys_client.load_extension(f"controller.{cmd_file.stem}")
                except errors.ExtensionAlreadyLoaded:
                    logger.info(f"{cmd_file.stem} command is already loaded")
                except Exception as ex:
                    logger.info(f"Error loading {cmd_file.stem} command: {ex}")

        
        guild = sys_client.get_guild(settings.GUILD_ID)

        #copy the global slash commands to the specific guild
        sys_client.tree.copy_global_to(guild=guild)
        await sys_client.tree.sync(guild=guild)


    #error handling
    @sys_client.event
    async def on_command_error(ctx, error):
        if isinstance(error, errors.ArgumentParsingError):
            await ctx.send("There is a parsing error")
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
    await sys_client.start(settings.DISCORD_API_SECRET, reconnect=True)

if __name__ == "__main__":
    asyncio.run(main())
