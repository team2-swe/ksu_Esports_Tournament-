import random
import numpy as np
from termcolor import colored
from discord.ext import commands
from discord import app_commands
import discord

class PrintBracket(commands.Cog):
    def __init__(self, bot:commands.bot):
        self.bot = bot
        self.teams = [
        {'team_name': 'Team A', 'players': ['Player A1', 'Player A2', 'Player A3', 'Player A4', 'Player A5']},
        {'team_name': 'Team B', 'players': ['Player B1', 'Player B2', 'Player B3', 'Player B4', 'Player B5']},
        {'team_name': 'Team C', 'players': ['Player C1', 'Player C2', 'Player C3', 'Player C4', 'Player C5']},
        {'team_name': 'Team D', 'players': ['Player D1', 'Player D2', 'Player D3', 'Player D4', 'Player D5']},
        {'team_name': 'Team E', 'players': ['Player E1', 'Player E2', 'Player E3', 'Player E4', 'Player E5']},
        {'team_name': 'Team F', 'players': ['Player F1', 'Player F2', 'Player F3', 'Player F4', 'Player F5']}
    ]
    @app_commands.command(name="bracket", description="Create check-in for a game")
    async def print_bracket(self, interaction: discord.Interaction):

        n = len(self.teams)
        rounds = int(np.log2(n)) if n % 2 == 0 else int(np.log2(n + 1))  # Adjust round count for odd number of self.teams
        
        bracket = []
        
        # Handle first round where there may be an odd number of self.teams
        while len(self.teams) % 2 != 0:  # If odd number of self.teams, one team automatically advances
            self.teams.append({'team_name': 'BYE', 'players': []})  # BYE team advances without playing
        
        # Generate each round
        for round_num in range(rounds):
            round_matches = []
            random.shuffle(self.teams)
            
            for i in range(0, len(self.teams), 2):
                if i + 1 < len(self.teams):
                    match = (self.teams[i], self.teams[i+1])  # Store the pair of self.teams
                else:
                    match = (self.teams[i], None)  # One team automatically advances (BYE)
                
                round_matches.append(match)
            bracket.append(round_matches)

            # Prepare winners for the next round
            winners = []
            for match in round_matches:
                if match[1] is None:  # If one team automatically advances due to BYE
                    winner = match[0]
                    winners.append({'team_name': winner['team_name'], 'players': []})
                else:
                    winners.append({'team_name': f"Winner of {match[0]['team_name']} vs {match[1]['team_name']}", 'players': []})
            
            random.shuffle(winners)
            self.teams = winners

        # Prepare the string for Discord
        bracket_text = ""
        
        for round_num, round_matches in enumerate(bracket):
            round_title = f"**Round {round_num + 1}**"
            bracket_text += f"\n{round_title}\n{'-' * 40}\n"
            
            for match in round_matches:
                if match[1] is None:  # Team with BYE
                    bracket_text += f"🟢 **{match[0]['team_name']}** vs **BYE**\n"
                    for player in match[0]['players']:
                        bracket_text += f"   {player}\n"
                    bracket_text += "\n"
                else:
                    bracket_text += f"🟢 **{match[0]['team_name']}**     vs     🔴 **{match[1]['team_name']}**\n"
                    
                    max_players = max(len(match[0]['players']), len(match[1]['players']))
                    for i in range(max_players):
                        player1 = match[0]['players'][i] if i < len(match[0]['players']) else ''
                        player2 = match[1]['players'][i] if i < len(match[1]['players']) else ''
                        bracket_text += f"{player1.ljust(20)}   {player2.ljust(20)}\n"
                    
                    bracket_text += "\n"
            
            bracket_text += f"{'-' * 40}\n"

        await interaction.response.send_message(bracket_text)
   

async def setup(bot):
    await bot.add_cog(PrintBracket(bot))