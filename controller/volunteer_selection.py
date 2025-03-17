import random
import asyncio
import discord
from discord.ext import commands

class VolunteerSelection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_volunteers(self, ctx, players_list):
        MAX_PLAYERS = 10  # The maximum number of players allowed
        if len(players_list) <= MAX_PLAYERS:
            return players_list  # If players are within the limit, return as is

        await ctx.send(f" We have **{len(players_list)} players**, but only **{MAX_PLAYERS}** are allowed! 🚨")
        await ctx.send("If you are willing to **withdraw**, please react with YES to this message.")

        # Send message and wait for reactions
        message = await ctx.send("React with YES to withdraw")
        await message.add_reaction("YES")

        def check_reaction(reaction, user):
            return user in players_list and str(reaction.emoji) == "YES" and reaction.message.id == message.id

        try:
            # Wait for reactions (10 seconds)
            while len(players_list) > MAX_PLAYERS:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=10.0, check=check_reaction)
                if user in players_list:
                    players_list.remove(user)  # Remove player from list
                    await ctx.send(f"YES {user.mention} has volunteered to withdraw!")

                # Stop checking if we reach 10 players
                if len(players_list) <= MAX_PLAYERS:
                    break

        except asyncio.TimeoutError:
            await ctx.send(" Time is up! Moving to random selection if needed.")

        # If still more than 10 players, randomly pick 10
        if len(players_list) > MAX_PLAYERS:
            players_list = random.sample(players_list, MAX_PLAYERS)
            await ctx.send("Too many players! Randomly selecting 10 players: " + ", ".join([p.mention for p in players_list]))

        return players_list

    @commands.command(name="select_volunteers")
    async def select_volunteers(self, ctx):
        # Simulating a list of players (Replace this with actual players)
        players_list = [member for member in ctx.guild.members if not member.bot]

        selected_players = await self.get_volunteers(ctx, players_list)
        await ctx.send("Final Selected Players: " + ", ".join([p.mention for p in selected_players]))

async def setup(bot):
    await bot.add_cog(VolunteerSelection(bot))
