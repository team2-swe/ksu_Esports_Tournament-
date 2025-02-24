import discord
from discord.ui import *
from config import settings
import traceback
import asyncio
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
        try:
            db = dbc_model.Tournament_DB()
            dbc_model.Player.register(db, interaction=interaction, gamename=self.game_name.value.strip(), tagid=self.Tag_id.value.strip())
            db.close_db()
            embed = discord.Embed(title="Checkin summury",
                                description=f"submitted game name: {self.game_name.value} and your tag id:{self.Tag_id.value}",
                                color=discord.Color.yellow())
            embed.set_author(name=self.user)
            await interaction.response.send_message(f"{self.user}, you have completed registration", embed=embed)

        except Exception as ex:
            print(f"it is faild on {ex}")

    async def on_error(self, interaction: discord.Interaction, error : Exception):
        traceback.print_tb(error.__traceback__)
        return await super().on_submit(interaction) 

class PreferenceSelect(discord.ui.Select):
    def __init__(self):
        options = [ 
                   discord.SelectOption(label="Top Lane", value="top"),
                   discord.SelectOption(label="Jungle", value="jungle"),
                   discord.SelectOption(label="Mid Lane", value="mid"),
                   discord.SelectOption(label="Bottom", value="bottom"),
                   discord.SelectOption(label="Support", value="support"),
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
    isRoleSelected : bool = False
    isPrefSelected : bool = False

    def __init__(self, *, timeout = 540):
        super().__init__(timeout=timeout)
        self.timeout = timeout

    @discord.ui.select(
        placeholder="select and set game details",
        options=[
            discord.SelectOption(label="your prefernce", value="pref"),
            discord.SelectOption(label="your role", value="role")
        ]
    )
    async def select_game_details(self, interaction:discord.Interaction, select_item : discord.ui.Select):
        if select_item.values[0] == "pref":
            self.children[0].disabled= True   
            game_select = PreferenceSelect()
            self.add_item(game_select)
            await interaction.message.edit(view=self)
            await interaction.response.defer()
            self.isPrefSelected = True
        else:
            self.children[0].disabled= True
            game_select = RoleSelect()
            self.add_item(game_select)
            await interaction.message.edit(view=self)
            await interaction.response.defer()
            self.isRoleSelected = True

    async def selected_preferences(self, interaction : discord.Interaction, choices):
        
        self.selected_pref = choices 
        self.children[1].disabled= True
        await interaction.message.edit(view=self)
        # await interaction.response.defer()
        
        if not self.isRoleSelected:
            game_select = RoleSelect()
            self.add_item(game_select)
            await interaction.message.edit(view=self)
            # await interaction.response.defer()
        
        db = dbc_model.Tournament_DB()
        dbc_model.Game.update_pref(db, interaction, self.selected_pref)
        db.close_db()
        self.stop()

    async def selected_role(self, interaction : discord.Interaction, choices):
        
        self.selected_role = choices 
        self.children[1].disabled= True
        await interaction.message.edit(view=self)
        await interaction.response.defer()

        if not self.isPrefSelected:
            game_select = PreferenceSelect()
            self.add_item(game_select)
            await interaction.message.edit(view=self)
            await interaction.response.defer()
        db = dbc_model.Tournament_DB()
        dbc_model.Game.update_role(db, interaction, self.selected_role)
        db.close_db()

class Checkin_RegisterModal(Modal, title="Registeration"):
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
            db = dbc_model.Tournament_DB()
            dbc_model.Player.register(db, interaction=interaction, gamename=self.game_name.value.strip(), tagid=self.Tag_id.value.strip())
            db.close_db()
            embed = discord.Embed(title="Checkin summury",
                                description=f"submitted game name: {self.game_name.value} and your tag id:{self.Tag_id.value}",
                                color=discord.Color.yellow())
            embed.set_author(name=self.user)

            await interaction.response.send_message(f"{self.user}, you have completed registration", ephemeral=True)

            role_pref_view = PlayerPrefRole()
            # await interaction.response.send_message(f"{self.user}, you have completed registration", embed=embed, ephemeral=True)
            message = await interaction.followup.send(view=role_pref_view)

            await asyncio.sleep(self.timeout)
            await message.delete()

        except Exception as ex:
            print(f"it is faild on {ex}")