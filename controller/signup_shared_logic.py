import discord
import traceback
import asyncio
# from view.checkIn_view import RegisterModal
from view.common_view import RegisterModal

class SharedLogic:
    async def __init__(self):
        pass
    
    @staticmethod
    async def execute_signup_model(interaction:discord.Interaction, timeout : int = 300):
        register_modal = RegisterModal()
        register_modal.user = interaction.user
        message = await interaction.response.send_modal(register_modal)

        await asyncio.sleep(timeout)
        await message.delete()


