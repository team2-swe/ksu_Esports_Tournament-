import discord
from discord.ui import *
from config import settings
import traceback
import asyncio
from model.button_state import ButtonState
from model.dbc_model import Player
from config import settings
from common.cached_details import Details_Cached
# from signUp_view import SignUpView
from common import common_scripts
import time
from model import dbc_model
from view.common_view import PlayerPrefRole
from controller.signup_shared_logic import SharedLogic

logger = settings.logging.getLogger("discord")

class CheckinView(discord.ui.View):
    def __init__(self, buttonState, timeout = 30):
        super().__init__(timeout=timeout)
        self.button_state = buttonState
        self.timeout = timeout
        self.viewStart_time = time.time()

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        #await self.message.delete()  --we can delete the messgae at all
        await self.message.edit(view=self)
        


    async def on_timeout(self) -> None:
        await self.message.channel.send(f"this action is timed out, please use a /register command to register")
        await self.disable_all_items()



    @discord.ui.button(label="Checkin", style=discord.ButtonStyle.success)
    async def Checkin(self, interaction: discord.Interaction, button:discord.ui.Button):
        user = interaction.user
        dm_to_user = await user.create_dm()
        remaining_time = self.timeout - (time.time() - self.viewStart_time)

        if Player.isAcountExist(interaction):
            # self.disable_all_items()
            player_preference_role_view = PlayerPrefRole()

            await dm_to_user.send(f"inprogress checkin.... please fill your prefernec and role for the game", view=player_preference_role_view)
            await interaction.response.send_message(f"your checkin inprogress..., Check your DMs for next step", ephemeral=True)

            await asyncio.sleep(self.timeout)
            await message.delete()
        else:
            button_state = ButtonState()
            signUp_view = SignUpView(button_state, timeout=remaining_time)

            if signUp_view.children:

                ksu_logo_path = await common_scripts.get_ksu_logo()
                resize_logo, logo_extention  = await common_scripts.ksu_img_resize(ksu_logo_path)
                # logo = discord.File(resize_logo, filename=resize_logo.name)

                logger.info(f"log path is : {resize_logo} and file name {logo_extention}")

                embed = discord.Embed(
                    color=discord.Colour.dark_teal(),
                    description="this is our server to play game .........................\
                    .................................................................\
                        ........................................................\
                            .................................",
                    title=f"welcome to {interaction.guild} server"
                )
                # embed.set_image(url=f"{ksu_logo_path}")
                embed.set_thumbnail(url=f"attachment://resized_logo{logo_extention}")
                
                message = await dm_to_user.send(f"inprogress checkin.... please register here", embed=embed, file=discord.File(resize_logo, filename=f"resized_logo{logo_extention}"), view=signUp_view)
                signUp_view.message = message
                signUp_view.isFromCheckin = True

                # await signUp_view.wait()
                await asyncio.sleep(self.timeout)
                await message.delete()

                await interaction.response.send_message(f"your checkin inprogress..., Check your DMs for next step", ephemeral=True)


            else:
                logger.error("signup view is not working please take a look")
                server_owner = interaction.guild.owner

                await server_owner.send(f"Hello {server_owner} the signup view is not working please check")


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("sure ignore for now")
        self.buttonState.set_button_state(True)
        self.stop()


class SignUpView(discord.ui.View):
    def __init__(self, buttonState, timeout = 200):
        super().__init__(timeout=timeout)
        self.button_state = buttonState
        self.timeout = timeout
        self.viewStart_time = time.time()

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        #await self.message.delete()  --we can delete the messgae at all
        await self.message.edit(view=self)
        


    async def on_timeout(self) -> None:
        await self.message.channel.send("this action is timed out, please use a /register command to register")
        await self.disable_all_items()

    @discord.ui.button(label="signUp", style=discord.ButtonStyle.success)
    async def signUp(self, interaction: discord.Interaction, button:discord.ui.Button):
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
        self.button_state.set_button_state(True)
        self.stop()
        await SharedLogic.execute_checkin_signup_model(interaction)
        await self.disable_all_items()
        # await interaction.response.send_message("Thnaks for submission")
        


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("sure ignore for now")
        self.button_state.set_button_state(True)
        self.stop()