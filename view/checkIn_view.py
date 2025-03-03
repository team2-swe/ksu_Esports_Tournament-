import discord
from discord.ui import *
from config import settings
import asyncio
from model.dbc_model import Tournament_DB, Player
from config import settings
from common import common_scripts
import time
from view.common_view import PlayerPrefRole
from controller.signup_shared_logic import SharedLogic

logger = settings.logging.getLogger("discord")

class CheckinView(discord.ui.View):
    def __init__(self, timeout = 900):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.viewStart_time = time.time()

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        #await self.message.delete()  --we can delete the messgae at all
        await self.message.edit(view=self)
        
    async def on_timeout(self) -> None:
        await self.user_dm.send("Check-In has timed out")
        await self.message.channel.send(f"Check-In has timed out")
        await self.disable_all_items()

    @discord.ui.button(label="Check-In", style=discord.ButtonStyle.success)
    async def Checkin(self, interaction: discord.Interaction, button:discord.ui.Button):
        user = interaction.user
        dm_to_user = await user.create_dm()
        self.user_dm = dm_to_user
        remaining_time = self.timeout - (time.time() - self.viewStart_time)

        db = Tournament_DB()
        isAcountExist: bool = Player.isAcountExist(db, interaction)
        db.close_db()

        if isAcountExist:
            # self.disable_all_items()
            player_preference_role_view = PlayerPrefRole(timeout=remaining_time)

            await dm_to_user.send(content="Please select your role and preferences", view=player_preference_role_view)
            await interaction.response.send_message(f"Hang tight! Processing your check-in..., Check your DMs for the next step", ephemeral=True)

            # await asyncio.sleep(self.timeout)
            # await message.delete()
        else:
            signUp_view = SignUpView(timeout=remaining_time)

            if signUp_view.children:

                ksu_logo_path = await common_scripts.get_ksu_logo()
                resize_logo, logo_extention  = await common_scripts.ksu_img_resize(ksu_logo_path)
                # logo = discord.File(resize_logo, filename=resize_logo.name)

                logger.info(f"Log path is: {resize_logo} and file name {logo_extention}")

                embed = discord.Embed(
                    color=discord.Colour.dark_teal(),
                    description="Thank you for joining the server, \
                    please register your player profile below \
                    so we can provide the best gaming experience possible \
                    \
                    \
                    Have any questions? Contact an Admin for more details!",
                    title=f"Welcome to {interaction.guild} server"
                )
                # embed.set_image(url=f"{ksu_logo_path}")
                embed.set_thumbnail(url=f"attachment://resized_logo{logo_extention}")
                
                message = await dm_to_user.send(f"Hello, please register here: ", embed=embed, file=discord.File(resize_logo, filename=f"resized_logo{logo_extention}"), view=signUp_view)
                signUp_view.message = message
                signUp_view.isFromCheckin = True

                # await signUp_view.wait()
                await asyncio.sleep(self.timeout)
                await message.delete()

                await interaction.response.send_message(f"Hang tight! Processing your check-in..., Check your DMs for next step", ephemeral=True)


            else:
                logger.error("Signup view is not working please take a look")
                server_owner = interaction.guild.owner

                await server_owner.send(f"Hello {server_owner} , the signup view is not working please go check")


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Registration Canceled")
        self.stop()


class SignUpView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.viewStart_time = time.time()

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def on_timeout(self) -> None:
        await self.disable_all_items()

    @discord.ui.button(label="Register", style=discord.ButtonStyle.success)
    async def signUp(self, interaction: discord.Interaction, button:discord.ui.Button):
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
        self.stop()
        await SharedLogic.execute_checkin_signup_model(interaction)
        await self.disable_all_items()
        # await interaction.response.send_message("Thanks for submission")
        


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Registration Canceled")
        self.stop()