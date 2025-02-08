import discord
from discord.ui import *
from config import settings
import traceback
import asyncio
from model.button_state import ButtonState
from model.dbc_model import Player
from config import settings
from common.cached_details import Details_Cached
from common import common_scripts
import time
from model import dbc_model

logger = settings.logging.getLogger("discord")

class RegisterModal(Modal, title="Registeration"):
    def __init__(self, timeout : int = 550):
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
            current_channel = interaction.channel

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
                #await interaction.response.send_message(f"Thank you, {self.user.nick}", ephemeral=True)

                player_preference_role_view = PlayerPrefRole(timeout=remaining_time)
                # message = await current_channel.send(view=player_preference_role_view)
                message = await interaction.response.send_message(view=player_preference_role_view)
                player_preference_role_view.message = message
                
                await asyncio.sleep(self.timeout)
                await message.delete()
                
                # await player_preference_role_view.wait()

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

    def __init__(self, *, timeout = 540):
        super().__init__(timeout=timeout)
        self.timeout = timeout
    
    # async def disable_all_items(self):
    #     for item in self.children:
    #         item.disabled = True
    #     #await self.message.delete()  --we can delete the messgae at all
    #     await self.message.edit(view=self)

    # async def on_timeout(self) -> None:
    #     await self.message.channel.send("this action is timed out, please use a command to register")
    #     await self.disable_all_items()

    @discord.ui.select(
        placeholder="select and set game details",
        options=[
            discord.SelectOption(label="your prefernce", value="pref"),
            discord.SelectOption(label="your role", value="role")
        ]
    )
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
