import discord, asyncio
from discord import app_commands
from discord.ext import commands
from view.checkIn_view import CheckinView
from config import settings
from common.cached_details import Details_Cached

logger = settings.logging.getLogger("discord")

class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="Checking to play next game")
    @app_commands.describe(timeout="Time in seconds before the command message freezes")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        # confirm_result = Player.fetch(interaction)
        if interaction.user.guild_permissions.administrator:
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
                await message.delete()

                await interaction.response.send_message(f"Check-In time has been completed")
            except discord.Forbidden:
                await channel.send(f"Bot does not have permission to send a message in {channel.name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Sorry you dont have access to use this command",
                                                    ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin_commands(bot))