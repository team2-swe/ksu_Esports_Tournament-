import discord
from discord import app_commands
from discord.ext import commands
from model.dbc_model import Player

class PlayerDetails(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="playersinfo", description="validating a player")
    async def player(self, interaction: discord.Interaction):
        confirm_result = Player.fetch(interaction)
        await interaction.response.send_message(f"your account {confirm_result.discord_id} is created")

async def setup(bot):
    await bot.add_cog(PlayerDetails(bot))