import random
import numpy as np
import discord
from discord import app_commands
from discord.ext import commands


class TournamentBracket(commands.Cog):
    def __init__(self, teams):
        self.teams = teams
        self.rounds = int(np.log2(len(teams))) if len(teams) % 2 == 0 else int(np.log2(len(teams) + 1))
        self.bracket = []
        self.generate_bracket()

    def generate_bracket(self):
        while len(self.teams) % 2 != 0:
            self.teams.append({'team_name': 'BYE', 'players': []})

        for round_num in range(self.rounds):
            round_matches = []
            random.shuffle(self.teams)

            for i in range(0, len(self.teams), 2):
                if i + 1 < len(self.teams):
                    match = (self.teams[i], self.teams[i+1])
                else:
                    match = (self.teams[i], None)
                round_matches.append(match)
            self.bracket.append(round_matches)

            winners = []
            for match in round_matches:
                if match[1] is None:
                    winner = match[0]
                    winners.append({'team_name': winner['team_name'], 'players': []})
                else:
                    winners.append({'team_name': f"Winner of {match[0]['team_name']} vs {match[1]['team_name']}", 'players': []})
            random.shuffle(winners)
            self.teams = winners

    def print_bracket(self):
        bracket_output = ""
        for round_num, round_matches in enumerate(self.bracket):
            round_title = f"**Round {round_num + 1}**"
            bracket_output += f"\n{round_title}\n{'-' * 40}\n"

            for match in round_matches:
                if match[1] is None:
                    bracket_output += f"**{match[0]['team_name']}** vs **BYE**\n"
                    for player in match[0]['players']:
                        bracket_output += f"   {player}\n"
                    bracket_output += "\n"
                else:
                    bracket_output += f"**{match[0]['team_name']}** vs **{match[1]['team_name']}**\n"
                    for player in match[0]['players']:
                        bracket_output += f"   {player}\n"
                    for player in match[1]['players']:
                        bracket_output += f"   {player}\n"
                    bracket_output += "\n"
        return bracket_output
    
    def generate_bracket_with_embed(self):
        embed = discord.Embed(title="Tournament Bracket", description="Here's the tournament bracket!", color=discord.Color.blue())
        for round_num, round_matches in enumerate(self.bracket):
            round_title = f"Round {round_num + 1}"
            round_field = ""
            for match in round_matches:
                if match[1] is None:
                    round_field += f"**{match[0]['team_name']}** vs **BYE**\n"
                    for player in match[0]['players']:
                        round_field += f"  - {player}\n"
                else:
                    round_field += f"**{match[0]['team_name']}** vs **{match[1]['team_name']}**\n"
                    for player in match[0]['players']:
                        round_field += f"  - {player}\n"
                    for player in match[1]['players']:
                        round_field += f"  - {player}\n"
            embed.add_field(name=round_title, value=round_field, inline=False)

        return embed
    
    def get_bracket(self):
        return self.bracket
    
    def get_teams(self):
        return self.teams
    
    def get_rounds(self):
        return self.rounds
    
    def get_team_names(self):
        return [team['team_name'] for team in self.teams]
    
    def get_team_players(self, team_name):
        for team in self.teams:
            if team['team_name'] == team_name:
                return team['players']
        return None
    
    def add_team(self, team_name, players):
        self.teams.append({'team_name': team_name, 'players': players})
        self.rounds = int(np.log2(len(self.teams))) if len(self.teams) % 2 == 0 else int(np.log2(len(self.teams) + 1))
        self.generate_bracket()

    def remove_team(self, team_name):
        for team in self.teams:
            if team['team_name'] == team_name:
                self.teams.remove(team)
                self.rounds = int(np.log2(len(self.teams))) if len(self.teams) % 2 == 0 else int(np.log2(len(self.teams) + 1))
                self.generate_bracket()
                return True
        return False
    
    def update_team(self, team_name, new_team_name, new_players):
        for team in self.teams:
            if team['team_name'] == team_name:
                team['team_name'] = new_team_name
                team['players'] = new_players
                return True
            
    
    def update_player(self, team_name, player_name, new_player_name):
        for team in self.teams:
            if team['team_name'] == team_name:
                for i, player in enumerate(team['players']):
                    if player == player_name:
                        team['players'][i] = new_player_name
                        return True
                    
    def add_player(self, team_name, player_name):
        for team in self.teams:
            if team['team_name'] == team_name:
                team['players'].append(player_name)
                return True 
        return False
    
    def remove_player(self, team_name, player_name):
        for team in self.teams:
            if team['team_name'] == team_name:
                team['players'].remove(player_name)
                return True
        return False
    
    def get_match(self, round_num, match_num):
        return self.bracket[round_num][match_num]
    
    def get_match_winner(self, round_num, match_num):
        return self.bracket[round_num][match_num][0]
    
    def get_match_loser(self, round_num, match_num):
        return self.bracket[round_num][match_num][1]
    
    def get_match_winner_name(self, round_num, match_num):
        return self.bracket[round_num][match_num][0]['team_name']
    
    def get_match_loser_name(self, round_num, match_num):
        if self.bracket[round_num][match_num][1] is None:
            return 'BYE'
        return self.bracket[round_num][match_num][1]['team_name']
    
    def get_match_players(self, round_num, match_num):
        players = []
        for team in self.bracket[round_num][match_num]:
            if team is not None:
                players.extend(team['players'])
        return players
    
    def get_match_winner_players(self, round_num, match_num):
        return self.bracket[round_num][match_num][0]['players']
    
    def get_match_loser_players(self, round_num, match_num):
        if self.bracket[round_num][match_num][1] is None:
            return []
        
        return self.bracket[round_num][match_num][1]['players']
    
    def set_match_winner(self, round_num, match_num, winner):
        self.bracket[round_num][match_num] = (winner, self.bracket[round_num][match_num][1])

    def set_match_loser(self, round_num, match_num, loser):
        self.bracket[round_num][match_num] = (self.bracket[round_num][match_num][0], loser)

    def set_match_winner_name(self, round_num, match_num, winner_name):
        self.bracket[round_num][match_num] = ({'team_name': winner_name, 'players': []}, self.bracket[round_num][match_num][1])

    def set_match_loser_name(self, round_num, match_num, loser_name):
        self.bracket[round_num][match_num] = (self.bracket[round_num][match_num][0], {'team_name': loser_name, 'players': []})

    def set_match_players(self, round_num, match_num, players):
        self.bracket[round_num][match_num] = ({'team_name': self.bracket[round_num][match_num][0]['team_name'], 'players': players}, self.bracket[round_num][match_num][1])

    def set_match_winner_players(self, round_num, match_num, players):
        self.bracket[round_num][match_num] = ({'team_name': self.bracket[round_num][match_num][0]['team_name'], 'players': players}, self.bracket[round_num][match_num][1])

    def set_match_loser_players(self, round_num, match_num, players):
        self.bracket[round_num][match_num] = (self.bracket[round_num][match_num][0], {'team_name': self.bracket[round_num][match_num][1]['team_name'], 'players': players})

    def get_winner(self):
        return self.bracket[-1][0]
    
    def get_winner_name(self):
        return self.bracket[-1][0]['team_name']
    
    def get_winner_players(self):
        return self.bracket[-1][0]['players']
    
    def set_winner(self, winner):
        self.bracket[-1][0] = winner

    def set_winner_name(self, winner_name):
        self.bracket[-1][0] = {'team_name': winner_name, 'players': []}

    def set_winner_players(self, players):
        self.bracket[-1][0] = {'team_name': self.bracket[-1][0]['team_name'], 'players': players}

    def get_loser(self):
        return self.bracket[-1][1]
    
    def get_loser_name(self):
        return self.bracket[-1][1]['team_name']
    
    def get_loser_players(self):
        return self.bracket[-1][1]['players']
    
    def set_loser(self, loser):
        self.bracket[-1][1] = loser

    def set_loser_name(self, loser_name):
        self.bracket[-1][1] = {'team_name': loser_name, 'players': []}

    def set_loser_players(self, players):
        self.bracket[-1][1] = {'team_name': self.bracket[-1][1]['team_name'], 'players': players}

    def get_round_winner(self, round_num):
        return [match[0] for match in self.bracket[round_num]]
    
    def get_round_winner_name(self, round_num):
        return [match[0]['team_name'] for match in self.bracket[round_num]]
    
    def get_round_winner_players(self, round_num):
        return [match[0]['players'] for match in self.bracket[round_num]]
    
    def set_round_winner(self, round_num, winners):
        for i, winner in enumerate(winners):
            self.bracket[round_num][i] = (winner, self.bracket[round_num][i][1])

    def set_round_winner_name(self, round_num, winners):
        for i, winner in enumerate(winners):
            self.bracket[round_num][i] = ({'team_name': winner, 'players': []}, self.bracket[round_num][i][1])

    def set_round_winner_players(self, round_num, winners):
        for i, winner in enumerate(winners):
            self.bracket[round_num][i] = ({'team_name': winner, 'players': []}, self.bracket[round_num][i][1])

    def get_round_loser(self, round_num):
        return [match[1] for match in self.bracket[round_num]]
    
    def get_round_loser_name(self, round_num):
        return [match[1]['team_name'] for match in self.bracket[round_num]]
    
    def get_round_loser_players(self, round_num):
        return [match[1]['players'] for match in self.bracket[round_num]]
    
    def set_round_loser(self, round_num, losers):
        for i, loser in enumerate(losers):
            self.bracket[round_num][i] = (self.bracket[round_num][i][0], loser)

    def set_round_loser_name(self, round_num, losers):
        for i, loser in enumerate(losers):
            self.bracket[round_num][i] = (self.bracket[round_num][i][0], {'team_name': loser, 'players': []})

    def set_round_loser_players(self, round_num, losers):
        for i, loser in enumerate(losers):
            self.bracket[round_num][i] = (self.bracket[round_num][i][0], {'team_name': loser, 'players': []})

    def get_round(self, round_num):
        return self.bracket[round_num]

    @app_commands.command(name="send_bracket_text", description="Send the tournament bracket in text format")
    async def send_bracket_text(self, ctx):
        await ctx.send(f"```\n{self.print_bracket()}```")
    # async def send_bracket(self, ctx):
    #     await ctx.send(embed=self.generate_bracket_with_embed())

async def setup(bot):
    bot.add_cog(TournamentBracket(bot))