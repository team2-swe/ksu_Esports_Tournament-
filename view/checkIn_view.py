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
        await self.message.channel.send("this action is timed out, please use a command to register")
        await self.disable_all_items()



    @discord.ui.button(label="Checkin", style=discord.ButtonStyle.success)
    async def Checkin(self, interaction: discord.Interaction, button:discord.ui.Button):
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
        if Player.isAcountExist(interaction):
            # self.disable_all_items()
            player_preference_role_view = PlayerPrefRole()

            await interaction.response.send_message(view=player_preference_role_view)
            await asyncio.sleep(self.timeout)
            await message.delete()
            # await self.channel.send(view=player_preference_role_view)
            # self.button_state.set_button_state(True)
            # self.stop()
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

                # guild_id = interaction.guild.id
                # channelName = settings.PLAYERES_CH
                # registeration_CH_Id = await Details_Cached.get_channel_id(channelName, guild_id)
                # channel = interaction.guild.get_channel(registeration_CH_Id)
                # await channel.send(embed=embed, file=discord.File(resize_logo, filename=f"resized_logo{logo_extention}"))
                # message = await channel.send(view=signUp_view)

                message = await interaction.response.send_message(embed=embed, file=discord.File(resize_logo, filename=f"resized_logo{logo_extention}"), view=signUp_view)
                # message = await interaction.response.send_message(view=signUp_view)

                signUp_view.message = message

                # await signUp_view.wait()
                await asyncio.sleep(self.timeout)
                await message.delete()

                await interaction.response.send_message(f"Checkin time has completed")

                # if button_state.buttons_state is None:
                #     logger.info(f"member id:{member.id} loged in the first time")

                # if button_state.buttons_state is True:
                #     logger.info(f"member id:{member.id} successfully sign up")

            else:
                logger.error("signup view is not working please take a look")
                server_owner = interaction.guild.owner

                await server_owner.send(f"Hello {server_owner} the signup view is not working please check")


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("sure ignore for now")
        self.buttonState.set_button_state(True)
        self.stop()

'''
class RegisterModal(Modal, title="Registeration"):
    def __init__(self, timeout=15):
        super().__init__()
        self.timeout = timeout
        self.viewStart_time = time.time()
        self.game_name = TextInput(
            style=discord.TextStyle.long,
            label="game name:",
            max_length=500,
            required=True,
            placeholder="game you would like to play"
        )
        self.add_item(self.game_name)

        self.Tag_id = TextInput(
            style=discord.TextStyle.short,
            label="your tag id",
            required=True,
            placeholder="your tag id for the game"
        )
        self.add_item(self.Tag_id)

    async def on_submit(self, interaction: discord.Interaction):
        """ this has a summury of checkin submission
        info:
            summury will be send to feedback channel
        Args:
            discord interaction (interaction: discord.Interaction)
        """
        logger.info(f"game detail {self.game_name.value} and user id is {self.Tag_id.value}")
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
        try:
            guild_id = interaction.guild.id
            channelName = settings.FEEDBACK_CH
            channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
            channel = interaction.guild.get_channel(channel_id)
            logger.info(f"####----member channel details guild_id: {guild_id}, ch_name: {channelName}, \
                        cha_id: {channel_id} interaction cha_id: {channel}")
            
            confirmation = dbc_model.Player.register(interaction=interaction, gamename=self.game_name.value.strip(), tagid=self.Tag_id.value.strip())
            if confirmation:
                embed = discord.Embed(title="Checkin summury",
                                    description=f"submitted game name: {self.game_name.value} and your tag id:{self.Tag_id.value}",
                                    color=discord.Color.yellow())
                embed.set_author(name=self.user.nick)

                await channel.send(embed=embed)
                # await interaction.response.send_message(embed=embed)
                await interaction.response.send_message(f"Thank you, {self.user.nick}", ephemeral=True)

                player_preference_role_view = PlayerPrefRole(timeout=remaining_time)
                message = await interaction.response.send_message(view=player_preference_role_view)
                player_preference_role_view.message = message
                await player_preference_role_view.wait()

        except Exception as ex:
            print(f"it is faild on {ex}")

    async def on_error(self, interaction: discord.Interaction, error : Exception):
        traceback.print_tb(error.__traceback__)
        return await super().on_submit(interaction) 

class PreferenceSelect(discord.ui.Select):
    def __init__(self):
        options = [ 
                   discord.SelectOption(label="1_top_priority", value="tp"),
                   discord.SelectOption(label="2_jungle_priority", value="jp"),
                   discord.SelectOption(label="3_mid_priority", value="mp"),
                   discord.SelectOption(label="4_bot_priority", value="bp"),
                   discord.SelectOption(label="5_support_priority", value="sp"),
        ]
        super().__init__(options=options, placeholder="select your prefernec in order, max 3", max_values=3)

    async def callback(self, interaction:discord.Interaction):
        await self.view.selected_preferences(interaction, self.values)

class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = [ 
                   discord.SelectOption(label="rol1", value="rol1"),
                   discord.SelectOption(label="rol2", value="rol2"),
                   discord.SelectOption(label="rol3", value="rol3"),
        ]
        super().__init__(options=options, placeholder="select your role", max_values=1)

    async def callback(self, interaction:discord.Interaction):
        await self.view.selected_role(interaction, self.values)       

class PlayerPrefRole(discord.ui.View):
    selected_pref = None 
    selected_role = None
    slected_list : list = {}

    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.timeout = timeout
    
    @discord.ui.select(
        placeholder="select and set game details",
        options=[
            discord.SelectOption(label="your prefernce", value="pref"),
            discord.SelectOption(label="your role", value="role")
        ]
        
    )
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        #await self.message.delete()  --we can delete the messgae at all
        await self.message.edit(view=self)
        


    async def on_timeout(self) -> None:
        await self.message.channel.send("this action is timed out, please use a command to register")
        await self.disable_all_items()

    async def select_game_details(self, interaction:discord.Interaction, select_item : discord.ui.Select):
        if select_item.values[0] == "pref" and "pref" not in self.slected_list: 
            self.slected_list['pref'] = True

            if select_item in select_item.options:
                if 'role' in select_item.label.lower():
                    self.children[0].disabled= True
                 
            game_select = PreferenceSelect()
            self.add_item(game_select)
            await interaction.message.edit(view=self)
            await interaction.response.defer()
        else:
            if 'pref' in select_item:
                self.children[0].disabled= True
            
            game_select = RoleSelect()
            self.add_item(game_select)
            await interaction.message.edit(view=self)
            await interaction.response.defer()

    async def selected_preferences(self, interaction : discord.Interaction, choices):
        self.selected_pref = choices 
        self.children[1].disabled= True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        self.stop()

    async def selected_role(self, interaction : discord.Interaction, choices):
        self.selected_role = choices 
        self.children[1].disabled= True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        self.stop()

'''

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
        await self.message.channel.send("this action is timed out, please use a command to register")
        await self.disable_all_items()

    @discord.ui.button(label="signUp", style=discord.ButtonStyle.success)
    async def signUp(self, interaction: discord.Interaction, button:discord.ui.Button):
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
        self.button_state.set_button_state(True)
        self.stop()
        await SharedLogic.execute_signup_model(interaction)
        await self.disable_all_items()
        # await interaction.response.send_message("Thnaks for submission")
        


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("sure ignore for now")
        self.button_state.set_button_state(True)
        self.stop()