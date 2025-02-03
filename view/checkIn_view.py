import discord
from discord.ui import *
from config import settings
import traceback

class CheckIn_view(View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)

    @button(label='Check In', style=discord.ButtonStyle.green)
    async def check_in(self, interaction: discord.Interaction, button: Button):
        #call the controller to handle the interaction here
        pass

import discord
from model.button_state import ButtonState

class CheckinView(discord.ui.View):
    def __init__(self, buttonState, timeout = 15):
        super().__init__(timeout=timeout)
        self.button_state = buttonState

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
        self.disable_all_items()
        player_preference_role_view = PlayerPrefRole()

        await interaction.response.send_message(view=player_preference_role_view)
        self.button_state.set_button_state(True)
        self.stop()


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("sure ignore for now")
        self.buttonState.set_button_state(True)
        self.stop()


class RegisterModal(Modal):
    def __init__(self, title: str = "register form"):
        super().__init__(title=title)

        game_name = TextInput(
            style=discord.TextStyle.short,
            label="Title",
            required=True,
            placeholder="game you would like to play"
        )

        details = TextInput(
            style=discord.TextStyle.long,
            label="Additional details",
            required=False,
            max_length=500,
            placeholder="comments"
        )

    async def on_submit(self, interaction: discord.Interaction):
        """ this has a summury of checkin submission
        info:
            summury will be send to feedback channel
        Args:
            discord interaction (interaction: discord.Interaction)
        """
        channel = interaction.guild.get_channel(settings.FEEDBACK_CH)
        embed = discord.Embed(title="Checkin summury",
                            description=self.message.value,
                            color=discord.Color.yellow())
        embed.set_author(name=self.user.nick)

        await channel.send(embed=embed)
        await interaction.response.send_message(f"Thank you, {self.user.nick}", ephemeral=True)

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
