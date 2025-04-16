import discord
from discord.ui import *
from config import settings
from model.dbc_model import Tournament_DB, Player_game_info
import ast

logger = settings.logging.getLogger("discord")

class Tier_drodown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=tier, value=tier) for tier in ast.literal_eval(settings.TIER_LIST)[:25]]
        super().__init__(options=options, placeholder="Select the tier", min_values=1, max_values=1)

    async def callback(self, interaction:discord.Interaction):
        await self.view.selected_tier(interaction, self.values)


class TierView(discord.ui.View):

    def __init__(self, player_id):
        super().__init__()
        self.playerId = player_id
        self.selectedTier = None
        self.add_item(Tier_drodown())

    async def selected_tier(self, interaction:discord.Interaction, choices):
        self.selectedTier = choices[0] 
        self.children[0].disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        #Update db with selectred tire
        db = Tournament_DB()
        Player_game_info.update_tier(db, self.playerId, self.selectedTier)
        db.close_db()

        self.stop()
        await interaction.followup.send(f"Player tier has been updated")