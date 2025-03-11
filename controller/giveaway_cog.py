import discord
from discord.ext import commands
from discord import app_commands
import random
from model.giveaway_model import GiveawayModel
from view.giveaway_view import GiveawayView
from config import settings

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.view = GiveawayView()
        self.model = GiveawayModel() 
              

    @app_commands.command(description="the first top playeres, number of player random pick")
    async def giveaway(self, interaction: discord.Interaction, top: int = int(settings.TOP_SCORER), random: int = int(settings.RANDOM_PICK)):
        try:
            await self.view.send_confirmation_message(interaction=interaction, top=top, random=random)
        except Exception as e:
            await interaction.response.send_message(f"We encountered an error: {e}")

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(Giveaway(bot))