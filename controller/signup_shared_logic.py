import discord
import traceback
import asyncio
# from view.checkIn_view import RegisterModal
from view.common_view import RegisterModal, Checkin_RegisterModal

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

    @staticmethod
    async def execute_checkin_signup_model(interaction:discord.Interaction, timeout : int = 300):
        register_modal = Checkin_RegisterModal()
        
        register_modal.user = interaction.user
        message = await interaction.response.send_modal(register_modal)

        await asyncio.sleep(timeout)
        await message.delete()

        # register_modal.time_out_task = asyncio.create_task(SharedLogic.timeout_task(timeout=timeout, message=message))


    @staticmethod
    async def timeout_task(timeout, message):
        await asyncio.sleep(timeout)

        try:
            await message.delete()
        except discord.NotFound:
            pass
        




