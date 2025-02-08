import discord, asyncio
from discord import app_commands
from discord.ext import commands
from model.dbc_model import Player
from view.checkIn_view import CheckinView
from model.button_state import ButtonState
from config import settings
from common.cached_details import Details_Cached

logger = settings.logging.getLogger("discord")

class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="checking to play next game")
    @app_commands.describe(timeout="time in second befor the command message frez")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        # confirm_result = Player.fetch(interaction)
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            channelName = settings.TOURNAMENT_CH
            channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
            channel = interaction.guild.get_channel(channel_id)
            try:
                logger.info(f"time out value is {timeout}")
                button_state = ButtonState()
                game_checkin_view = CheckinView(button_state, timeout=timeout)  

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

                await interaction.response.send_message(f"Checkin time has completed")
            except discord.Forbidden:
                await channel.send(f"Bot doenst have a permission to send a message in {channel.name}", ephemeral=True)

            if button_state.buttons_state is None:
                logger.info(f"member id:{interaction.user} loged in")

            if button_state.buttons_state is True:
                logger.info(f"member id:{interaction.id} successfully signin")

        else:
            await interaction.response.send_message(f"Sorry you dont have required permission to use this command", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin_commands(bot))