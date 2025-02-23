from collections import defaultdict
import copy

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

        player["RoleBasedPerformance"] = playerPerfomanceOfRole

        players_output.append(player)
    return players_output
async def relativePerformance(Tier, Role_preference):
    playerPerfomanceOfRole = {}
    SkillFactor_set = {"Default": 0.0, "Iron": 1.0, "Bronze": 1.05, "Silver": 1.10, "Gold": 1.15, "Platinum": 1.20,
                       "Emerald": 1.25, "Diamond": 1.30, "Master": 1.35, "Grandmaster": 1.40, "Challenger": 1.45}

    #get player skill factor based on their Tier
    player_skillFactor = SkillFactor_set.get(Tier)

    #to calculate the relative performance of each player based on their Tier and Role_preference
    totalRolePlayerSelected = 0
    for i, Role in enumerate(Role_preference):
        pref_penality = i*5

        relative_performance = player_skillFactor*0.75 + (1- pref_penality/100)*0.25
        playerPerfomanceOfRole[Role] = relative_performance
        totalRolePlayerSelected+=1

    if(totalRolePlayerSelected <= 5):
        playerPerfomanceOfRole['forced'] = player_skillFactor*0.75

    return playerPerfomanceOfRole

def teamPerformance(team):
    totalRelativePerformance = 0
    for player in team:
        totalRelativePerformance += sum(player["RoleBasedPerformance"].values())
    return totalRelativePerformance

def possible_assighn_Role(player, teamRoleSet):
    for Role, performance in player["RoleBasedPerformance"].items():
        if Role not in teamRoleSet:
            return Role, performance
        if Role == "forced":
            return Role, performance
    return None, None

def isPlayerRoleprefered(player, nextPlayer, Role):
    return player["RoleBasedPerformance"].get(Role, 0) > nextPlayer["RoleBasedPerformance"].get(Role, 0)

def assignPlayer_toTeam(player, team1, team2, team1_Roles, team2_Roles):
    Role, performance = possible_assighn_Role(player, team1_Roles)
    if Role and performance:
        team1.append(player)
        team1_Roles.add(Role)
        return "T1"
    
    Role, performance = possible_assighn_Role(player, team2_Roles)
    if Role and performance:
        team2.append(player)
        team2_Roles.add(Role)
        return "T2"
    
    return None

def buildTeams(players):
    team1, team2 = [], []
    team1_Roles, team2_Roles = set(), set()
    t1_performance = 0
    t2_performance = 0
    for player in players:
        player_index = players.index(player)
        next_player = players[player_index + 1] if player_index + 1 < len(players) else None

        Role_assigned_to = {}
        if len(team1) != 0 and len(team2) <= len(team1):
            if t2_performance <= t1_performance:
                Role, performance = possible_assighn_Role(player, team2_Roles)
                Role_assigned_to["team_Role"] = Role
                Role_assigned_to["assigned_to"] = player
                if Role:
                    # next_player = next((p for p in players if p != player), None)
                    if next_player:
                        next_player_Role, next_player_performance = possible_assighn_Role(next_player, team2_Roles)
                        if next_player_Role and performance >= next_player_performance:
                            team2.append(Role_assigned_to)
                            team2_Roles.add(Role)
                            t2_performance += performance
                            continue
                        else:
                            team1.append(Role_assigned_to)
                            team1_Roles.add(Role)
                            t1_performance += performance
                    else:
                        team2.append(Role_assigned_to)
                        team2_Roles.add(Role)
            else:
                Role, performance = possible_assighn_Role(player, team1_Roles)
                Role_assigned_to["team_Role"] = Role
                Role_assigned_to["assigned_to"] = player
                if Role:
                    team1.append(Role_assigned_to)
                    team1_Roles.add(Role)
                    t1_performance += performance
        else:
            if t1_performance <= t2_performance:
                Role, performance = possible_assighn_Role(player, team1_Roles)
                Role_assigned_to["team_Role"] = Role
                Role_assigned_to["assigned_to"] = player
                if Role:
                    # next_player = next((p for p in players if p != player), None)
                    if next_player:
                        next_player_Role, next_player_performance = possible_assighn_Role(next_player, team1_Roles)
                        if next_player_Role and performance >= next_player_performance:
                            team1.append(Role_assigned_to)
                            team1_Roles.add(Role)
                            t1_performance += performance
                            continue
                        else:
                            team2.append(Role_assigned_to)
                            team2_Roles.add(Role)
                            t2_performance += performance
                    else:
                        team1.append(Role_assigned_to)
                        team1_Roles.add(Role)
            else:
                Role, performance = possible_assighn_Role(player, team2_Roles)
                Role_assigned_to["team_Role"] = Role
                Role_assigned_to["assigned_to"] = player
                if Role:
                    team2.append(Role_assigned_to)
                    team2_Roles.add(Role)
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

    for player in T2:
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



orginal_players = [
    {'user_id': 'player1', 'Tier': 'Platinum', 'Rank': 'II', 'WR': 56, 'Role': ['Mid','Top','Jungle']},
    {'user_id': 'player2', 'Tier': 'Gold', 'Rank': 'II', 'Role': ['Support','Mid'], 'WR': 73},
    {'user_id': 'player3', 'Tier': 'Platinum', 'Rank': 'IV', 'WR': 77, 'Role': ['Bottom','Top','Jungle','Mid','Support']},
    {'user_id': 'player4', 'Tier': 'Bronze', 'Rank': 'III', 'WR': 78, 'Role': ['Jungle']},
    {'user_id': 'player5', 'Tier': 'Gold', 'Rank': 'I', 'WR': 69, 'Role': ['Top','Jungle','Mid']},
    {'user_id': 'player6', 'Tier': 'Bronze', 'Rank': 'I', 'WR': 86, 'Role': ['Top','Jungle']},
    {'user_id': 'player7', 'Tier': 'Gold', 'Rank': 'IV', 'WR': 47, 'Role': ['Bottom','Mid','Top','Jungle','Support']},
    {'user_id': 'player8', 'Tier': 'Platinum', 'Rank': 'V', 'WR': 47, 'Role': ['Mid']},
    {'user_id': 'player9', 'Tier': 'Diamond', 'Rank': 'II', 'WR': 75, 'Role': ['Mid','Top','Jungle']},
    {'user_id': 'player10', 'Tier': 'Master', 'Rank': 'II', 'WR': 93, 'Role': ['Top','Bottom','Jungle','Support']}
]


async def main():
    sorted_player = await intialSortingPlayer(players=orginal_players)
    print(sorted_player)
    # player_performance = await performance(sorted_player)
    # print(player_performance)
    # t1, t2 = buildTeams(player_performance)
    # print(f"###team1 {t1}, \n #####team2 {t2}")


import asyncio
asyncio.run(main())