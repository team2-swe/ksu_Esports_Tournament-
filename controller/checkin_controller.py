import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from view.checkIn_view import CheckinView
from config import settings
from common.cached_details import Details_Cached

logger = settings.logging.getLogger("discord")

class CheckinController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="checking to play next game")
    @app_commands.describe(timeout="time in second befor the command message frez")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            channelName = settings.TOURNAMENT_CH

            # Try to find the channel directly first
            for channel in interaction.guild.channels:
                if channel.name == channelName and isinstance(channel, discord.TextChannel):
                    logger.info(f"Found channel directly: {channel.name} with ID {channel.id}")
                    try:
                        logger.info(f"time out value is {timeout}")
                        game_checkin_view = CheckinView(timeout=timeout)

                        message = await channel.send(view=game_checkin_view)
                        game_checkin_view.message = message
                        game_checkin_view.channel = channel

                        await interaction.response.send_message(f"Invitation successfully sent to {channel.name}")

                        await asyncio.sleep(timeout)
                        await message.delete()

                        return
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            f"Bot doesn't have permission to send a message in {channel.name}", ephemeral=True)
                        return

            # Fallback to cached channel ID if direct search fails
            channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
            if channel_id:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    try:
                        logger.info(f"time out value is {timeout}")
                        game_checkin_view = CheckinView(timeout=timeout)
                        message = await channel.send(view=game_checkin_view)
                        game_checkin_view.message = message
                        game_checkin_view.channel = channel
                        await interaction.response.send_message(f"Invitation successfully sent to {channel.name}")

                        await asyncio.sleep(timeout)
                        await message.delete()

                        return
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            f"Bot doesn't have permission to send a message in {channel.name}", ephemeral=True)
                        return

            # If we get here, we couldn't find the channel
            await interaction.response.send_message(
                f"Could not find channel named '{channelName}'. Available channels: {', '.join([ch.name for ch in interaction.guild.channels if isinstance(ch, discord.TextChannel)])}",
                ephemeral=True)
        else:
            await interaction.response.send_message(f"Sorry you dont have required permission to use this command",
                                                  ephemeral=True)


async def setup(bot):
    await bot.add_cog(CheckinController(bot))