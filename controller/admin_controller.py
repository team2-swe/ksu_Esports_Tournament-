import discord, asyncio
from discord import app_commands
from discord.ext import commands
from model.dbc_model import Player
from view.checkIn_view import CheckinView
from model.button_state import ButtonState
from config import settings

logger = settings.logging.getLogger("discord")

class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin", description="checking to play next game")
    async def checkin(self, interaction: discord.Interaction):
        # confirm_result = Player.fetch(interaction)

        button_state = ButtonState()
        signUp_view = CheckinView(button_state)  

        await interaction.response.send_message("check in instruction: the checkin time is ready")
        message = await interaction.followup.send(view=signUp_view)
        signUp_view.message = message

        await signUp_view.wait()
        # timeOut_duration =  10

        #wait the time out to be expired
        # await asyncio.sleep(timeOut_duration)

        # await message.delete()

        if button_state.buttons_state is None:
            logger.info(f"member id:{interaction.user} loged in")

        if button_state.buttons_state is True:
            logger.info(f"member id:{interaction.id} successfully signin")


async def setup(bot):
    await bot.add_cog(Admin_commands(bot))