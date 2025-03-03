import asyncio
from collections import defaultdict
import copy
import asyncio
from colorama import Fore, Style

""" Initial step sort player based on Tier, Rank and win ratio based on
    step1: sort based on player Tier
    step2: if players have same Tier sort based on Rank
    step3: if players have same Tier & Rank then sort based on WR
"""
async def intialSortingPlayer(players):
    #define custom order of Tier & Rank
    Tier_order = {"Challenger": 1, "Grandmaster": 2, "Master": 3, "Diamond": 4, "Emerald": 5, "Platinum": 6, "Gold": 7,
                  "Silver": 8, "Bronze": 9, "Iron": 10, "Default": 11}
    Rank_order = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}

    sortedPlayers = sorted(players, key=lambda pl: (Tier_order[pl['Tier']], Rank_order[pl['Rank']], -pl['WR']))
    
    return sortedPlayers

""" for sorted player calculate their relative performance based on their Role preference order
    Assumption: player effective output according to their Role preference is 5% reduce
                set SkillFactor_set for each Tier based on different considerations, and each skill 
                    has 5% skill advance/difference than the next Tier

    A standard mathematical formula for player skill factor based on the above assumptions and conditions
        relative_performance = player_skillFactor*0.75 + (1- pref_penalty/100)*0.25

    for player doesnt have Role preference then the forced assigned Role set as player PerformanceOfRole['forced']
"""
async def performance(players):
    players_output = []
    SkillFactor_set = {"Default": 0.0, "Iron": 1.0, "Bronze": 1.05, "Silver": 1.10, "Gold": 1.15, "Platinum": 1.20,
                       "Emerald": 1.25, "Diamond": 1.30, "Master": 1.35, "Grandmaster": 1.40, "Challenger": 1.45}

    for player in players:
        playerPerfomanceOfRole = {}
        player_Role = player["Role"]
        #get player skill factor based on their Tier
        player_skillFactor = SkillFactor_set.get(player["Tier"])

        #to calculate the relative performance of each player based on their Tier and Role_preference
        totalPlayerRolesProcessd = 0
        for i, Role in enumerate(player_Role):
            pref_penality = i*5

            relative_performance = player_skillFactor*0.75 + (1- pref_penality/100)*0.25
            playerPerfomanceOfRole[Role] = relative_performance
            totalPlayerRolesProcessd += 1

        if(totalPlayerRolesProcessd < 5):
            playerPerfomanceOfRole['forced'] = player_skillFactor*0.75

        player["roleBasedPerformance"] = playerPerfomanceOfRole

        players_output.append(player)
    return players_output
async def relativePerformance(tier, role_preference):
    playerPerfomanceOfRole = {}
    SkillFactor_set = {"Default": 0.0, "Iron": 1.0, "Bronze": 1.05, "Silver": 1.10, "Gold": 1.15, "Platinum": 1.20,
                       "Emerald": 1.25, "Diamond": 1.30, "Master": 1.35, "Grandmaster": 1.40, "Challenger": 1.45}

    #get player skill factor based on their tier
    player_skillFactor = SkillFactor_set.get(tier)

    #to calculate the relative performance of each player based on their Tier and Role_preference
    totalRolePlayerSelected = 0
    for i, role in enumerate(role_preference):
        pref_penality = i*5

        relative_performance = player_skillFactor*0.75 + (1- pref_penality/100)*0.25
        playerPerfomanceOfRole[role] = relative_performance
        totalRolePlayerSelected+=1

    if(totalRolePlayerSelected <= 5):
        playerPerfomanceOfRole['forced'] = player_skillFactor*0.75

    return playerPerfomanceOfRole

def teamPerformance(team):
    totalRelativePerformance = 0
    for player in team:
        totalRelativePerformance += sum(player["RoleBasedPerformance"].values())
    return totalRelativePerformance

def possible_assighn_role(player, teamRoleSet):
    for role, performance in player["roleBasedPerformance"].items():
        if role not in teamRoleSet:
            return role, performance
        if role == "forced":
            return role, performance
    return None, None

def isPlayerRoleprefered(player, nextPlayer, role):
    return player["roleBasedPerformance"].get(role, 0) > nextPlayer["roleBasedPerformance"].get(role, 0)

def assignPlayer_toTeam(player, team1, team2, team1_roles, team2_roles):
    role, performance = possible_assighn_role(player, team1_roles)
    if role and performance:
        team1.append(player)
        team1_roles.add(role)
        return "T1"
    
    role, performance = possible_assighn_role(player, team2_roles)
    if role and performance:
        team2.append(player)
        team2_roles.add(role)
        return "T2"
    
    return None

def buildTeams(players):
    team1, team2 = [], []
    team1_roles, team2_roles = set(), set()
    t1_performance = 0
    t2_performance = 0
    for player in players:
        player_index = players.index(player)
        next_player = players[player_index + 1] if player_index + 1 < len(players) else None

        role_assigned_to = {}
        if len(team1) != 0 and len(team2) <= len(team1):
            if t2_performance <= t1_performance:
                role, performance = possible_assighn_role(player, team2_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    # next_player = next((p for p in players if p != player), None)
                    if next_player:
                        next_player_role, next_player_performance = possible_assighn_role(next_player, team2_roles)
                        if next_player_role and performance >= next_player_performance:
                            team2.append(role_assigned_to)
                            team2_roles.add(role)
                            t2_performance += performance
                            continue
                        else:
                            role, performance = possible_assighn_role(player, team1_roles)
                            role_assigned_to["team_role"] = role
                            role_assigned_to["assigned_to"] = player
                            team1.append(role_assigned_to)
                            team1_roles.add(role)
                            t1_performance += performance
                    else:
                        team2.append(role_assigned_to)
                        team2_roles.add(role)
            else:
                role, performance = possible_assighn_role(player, team1_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    team1.append(role_assigned_to)
                    team1_roles.add(role)
                    t1_performance += performance
        else:
            if t1_performance <= t2_performance:
                role, performance = possible_assighn_role(player, team1_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    # next_player = next((p for p in players if p != player), None)
                    if next_player:
                        next_player_role, next_player_performance = possible_assighn_role(next_player, team1_roles)
                        if next_player_role and performance >= next_player_performance:
                            team1.append(role_assigned_to)
                            team1_roles.add(role)
                            t1_performance += performance
                            continue
                        else:
                            role, performance = possible_assighn_role(player, team2_roles)
                            role_assigned_to["team_role"] = role
                            role_assigned_to["assigned_to"] = player
                            team2.append(role_assigned_to)
                            team2_roles.add(role)
                            t2_performance += performance
                    else:
                        team1.append(role_assigned_to)
                        team1_roles.add(role)
            else:
                role, performance = possible_assighn_role(player, team2_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    team2.append(role_assigned_to)
                    team2_roles.add(role)
                    t2_performance += performance
                    
    return team1, team2


"""this is to makes sure same player not teamed up for tournaments
    method: verify_swap_teams
        grouping each team based on their respective game history based on (gameid/custoMid)

"""
def verify_swap_teams(t1, t2):
    group_t1 = defaultdict(list)
    group_t2 = defaultdict(list)

    for player in t1:
        for player_name, gameid in player.items():
            group_t1[gameid].append(player_name)

    for player in t2:
        for player_name, gameid in player.items():
            group_t2[gameid].append(player_name)

    for gameid in group_t1:
        if len(group_t1[gameid]) > 2:
            if gameid not in group_t2:
                players_t1 = group_t1[gameid]
                players_t2 = group_t2.get(gameid, [])
               
                for i in range(len(players_t1)):
                    if i < len(players_t2):
                        t1 = [player if player != players_t1[i] else {players_t2[i]: gameid} for player in t1]
                        t2 = [player if player != players_t2[i] else {players_t1[i]: gameid} for player in t2]

    for gameid in group_t2:
        if len(group_t2[gameid]) > 2:
            if gameid not in group_t1:
                players_t2 = group_t2[gameid]
                players_t1 = group_t1.get(gameid, [])
                
                for i in range(len(players_t2)):
                    if i < len(players_t1):
                        t1 = [player if player != players_t1[i] else {players_t2[i]: gameid} for player in t1]
                        t2 = [player if player != players_t2[i] else {players_t1[i]: gameid} for player in t2]

    return t1, t2



"""
async def main():
    sorted_player = await intialSortingPlayer(players=orginal_players)
    # print(sorted_player)
    player_performance = await performance(sorted_player)
    # print(player_performance)
    t1, t2 = buildTeams(player_performance)
    print(f"###team1 {t1}, \n #####team2 {t2}")


import asyncio
asyncio.run(main())
"""

# Define role_colors and rank_colors mappings
role_colors = {
    "tank": Fore.BLUE,
    "healer": Fore.GREEN,
    "dps": Fore.RED,
    # Add other roles as needed
}

rank_colors = {
    "bronze": Fore.YELLOW,
    "silver": Fore.WHITE,
    "gold": Fore.LIGHTYELLOW_EX,
    "platinum": Fore.LIGHTWHITE_EX,
    "diamond": Fore.CYAN,
    "master": Fore.MAGENTA,
    "grandmaster": Fore.LIGHTMAGENTA_EX,
    # Add other ranks as needed
}

def format_player_info(player_entry):
    """
    Returns a formatted string showing the player's tier, rank, assigned role, and their role preferences.
    Colors are applied according to the role and rank mappings.
    """
    assigned_player = player_entry["assigned_to"]
    assigned_role = player_entry.get("team_role", "N/A")
    # Capitalize each field
    player_id = assigned_player["player_id"].capitalize()
    tier = assigned_player["tier"].capitalize()
    rank = assigned_player["rank"]

    # Color the rank using Colorama mapping
    colored_rank = f"{rank_colors.get(rank, '')}{rank}{Style.RESET_ALL}"

    # Process and color each role in the player's preference list (capitalize them)
    colored_roles = []
    for role in assigned_player["role"]:
        role_lower = role.lower()
        color = role_colors.get(role_lower, "")
        colored_roles.append(f"{color}{role.capitalize()}{Style.RESET_ALL}")
    colored_roles_str = ", ".join(colored_roles)

    # Process the assigned role (capitalize) and color it
    assigned_role_str = assigned_role.capitalize() if assigned_role != "N/A" else "N/A"
    assigned_role_lower = assigned_role.lower() if assigned_role != "N/A" else "N/A"
    assigned_role_color = role_colors.get(assigned_role_lower, "")
    colored_assigned_role = f"{assigned_role_color}{assigned_role_str}{Style.RESET_ALL}" if assigned_role != "N/A" else "N/A"

    # Build the output string with the Assigned Role in the first column.
    return (f"Assigned Role: {colored_assigned_role} | "
            f"User: {player_id} | Tier: {tier} | Rank: {colored_rank} | Roles: {colored_roles_str}")


def print_team(team, team_name, color_output=False):
    print(f"========== {team_name} =============")
    for player in team:
        if color_output:
            print(format_player_info(player))
        else:
            assigned = player["assigned_to"]
            print(f"Assigned Role: {player.get('team_role', 'N/A')} | User: {assigned['player_id']} | "
                  f"Tier: {assigned['tier']} | Rank: {assigned['rank']} | Roles: {', '.join(assigned['role'])}")

orginal_players = [
    {'player_id': 'player1', 'Tier': 'Platinum', 'Rank': 'II', 'WR': 56, 'Role': ['Mid','Top','Jungle']},
    {'player_id': 'player2', 'Tier': 'Gold', 'Rank': 'II', 'Role': ['Support','Mid'], 'WR': 73},
    {'player_id': 'player3', 'Tier': 'Platinum', 'Rank': 'IV', 'WR': 77, 'Role': ['Bottom','Top','Jungle','Mid','Support']},
    {'player_id': 'player4', 'Tier': 'Bronze', 'Rank': 'III', 'WR': 78, 'Role': ['Jungle']},
    {'player_id': 'player5', 'Tier': 'Gold', 'Rank': 'I', 'WR': 69, 'Role': ['Top','Jungle','Mid']},
    {'player_id': 'player6', 'Tier': 'Bronze', 'Rank': 'I', 'WR': 86, 'Role': ['Top','Jungle']},
    {'player_id': 'player7', 'Tier': 'Gold', 'Rank': 'IV', 'WR': 47, 'Role': ['Bottom','Mid','Top','Jungle','Support']},
    {'player_id': 'player8', 'Tier': 'Platinum', 'Rank': 'V', 'WR': 47, 'Role': ['Mid']},
    {'player_id': 'player9', 'Tier': 'Diamond', 'Rank': 'II', 'WR': 75, 'Role': ['Mid','Top','Jungle']},
    {'player_id': 'player10', 'Tier': 'Master', 'Rank': 'II', 'WR': 93, 'Role': ['Top','Bottom','Jungle','Support']}
]


def format_player_info(player_entry):
    """
    Returns a formatted string showing the player's tier, rank, assigned role, and their role preferences.
    Colors are applied according to the role and rank mappings.
    """
    assigned_player = player_entry["assigned_to"]
    assigned_role = player_entry.get("team_role", "N/A")
    # Capitalize each field
    player_id = assigned_player["player_id"].capitalize()
    tier = assigned_player["tier"].capitalize()
    rank = assigned_player["rank"]

    # Color the rank using Colorama mapping
    colored_rank = f"{rank_colors.get(rank, '')}{rank}{Style.RESET_ALL}"

    # Process and color each role in the player's preference list (capitalize them)
    colored_roles = []
    for role in assigned_player["role"]:
        role_lower = role.lower()
        color = role_colors.get(role_lower, "")
        colored_roles.append(f"{color}{role.capitalize()}{Style.RESET_ALL}")
    colored_roles_str = ", ".join(colored_roles)

    # Process the assigned role (capitalize) and color it
    assigned_role_str = assigned_role.capitalize() if assigned_role != "N/A" else "N/A"
    assigned_role_lower = assigned_role.lower() if assigned_role != "N/A" else "N/A"
    assigned_role_color = role_colors.get(assigned_role_lower, "")
    colored_assigned_role = f"{assigned_role_color}{assigned_role_str}{Style.RESET_ALL}" if assigned_role != "N/A" else "N/A"

    # Build the output string with the Assigned Role in the first column.
    return (f"Assigned Role: {colored_assigned_role} | "
            f"User: {player_id} | Tier: {tier} | Rank: {colored_rank} | Roles: {colored_roles_str}")


def print_team(team, team_name, color_output=False):
    print(f"========== {team_name} =============")
    for player in team:
        if color_output:
            print(format_player_info(player))
        else:
            assigned = player["assigned_to"]
            print(f"Assigned Role: {player.get('team_role', 'N/A')} | User: {assigned['player_id']} | "
                  f"Tier: {assigned['tier']} | Rank: {assigned['rank']} | Roles: {', '.join(assigned['role'])}")

async def main(debug=False, color_output=False):
    sorted_player = await intialSortingPlayer(players=orginal_players)
    if debug:
        player_performance = await performance(sorted_player)
        t1, t2 = buildTeams(player_performance)
        print_team(t1, "Team 1", color_output)
        print_team(t2, "Team 2", color_output)
    else:
        print("Debug flag not enabled. No team output.")


asyncio.run(main(debug=False, color_output=False))
