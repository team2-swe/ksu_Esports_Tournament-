import discord, asyncio
import re
from discord import app_commands
from discord.ext import commands
from view.checkIn_view import CheckinView
from view.tier_view import TierView
from config import settings
from common.cached_details import Details_Cached
from model.dbc_model import Tournament_DB, Player_game_info, Checkin

logger = settings.logging.getLogger("discord")

class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="Create check-in for a game")
    @app_commands.describe(timeout="Time in seconds before the command message freezes")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        # confirm_result = Player.fetch(interaction)
        if interaction.user.guild_permissions.administrator:
            db= Tournament_DB()
            Checkin.createTable(db)
            db.close_db()

            guild_id = interaction.guild.id
            channelName = settings.TOURNAMENT_CH
            channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
            channel = interaction.guild.get_channel(channel_id)
            try:
                logger.info(f"Time out value is: {timeout}")
                game_checkin_view = CheckinView(timeout=timeout)  

                # await interaction.response.send_message("check in instruction: the checkin time is ready")
                # message = await interaction.followup.send(view=signUp_view)
                # signUp_view.message = message

                # await signUp_view.wait()
                message = await channel.send(view=game_checkin_view)
                game_checkin_view.message = message
                game_checkin_view.channel = channel

                await interaction.response.send_message(f"Invitation successfully sent")

                await asyncio.sleep(timeout)
                # await message.delete()
                await interaction.followup.send(f"Check-In time has been completed")
                # await interaction.response.send_message(f"Check-In time has been completed")
            except discord.Forbidden:
                await channel.send(f"Bot does not have permission to send a message in {channel.name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Sorry you dont have access to use this command",
                                                    ephemeral=True)

    @app_commands.command(name="updatetier", description="overwrite player tier")
    async def tier_update(self, interaction: discord.Interaction, player_id: str):
        if interaction.user.guild_permissions.administrator:
            id = await self.passingPlayerId(player_id.strip())
            if id is None:
                await interaction.response.send_message(f"Please provide a valid player id")
                return
            
            db = Tournament_DB()
            result = Player_game_info.fetch_by_id(db, id)
            db.close_db()
            if result is not None:
                player_tier = result[0][0]
                
                tierDropdownView = TierView(id)
                await interaction.response.send_message(f"player current tier is {player_tier} select the tier from dropdown", view=tierDropdownView)
            else:
                await interaction.response.send_message(f"Player not found, please check the user id")
        else:
            await interaction.response.send_message(f"Sorry you dont have access to use this command",
                                                    ephemeral=True)

    async def passingPlayerId(self, param):
        if param is not None:
            if isinstance(param, int):
                return param
            elif isinstance(param, str):
                if 1 <= len(param) <= 32:
                    if re.match("^[a-z0-9-_]+$", param):
                        return int(param)
                    return None
                return None
            else:
                return None
        return None
    

    async def cog_check(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command is only available in a server.")
            return False
        return True
    
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command is on cooldown, please try again in {error.retry_after:.2f} seconds.")
        else:
            raise error
        
async def setup(bot):
    await bot.add_cog(Admin_commands(bot))