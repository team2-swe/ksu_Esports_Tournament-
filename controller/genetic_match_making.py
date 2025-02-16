import asyncio
import random


async def intialSortingPlayer(players):
    # define custom order of tier & rank
    tier_order = {"challenger": 1, "grandmaster": 2, "master": 3, "diamond": 4, "emerald": 5, "platinum": 6, "gold": 7,
                  "silver": 8, "bronze": 9, "iron": 10, "default": 11}
    rank_order = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}

    sortedPlayers = sorted(players, key=lambda pl: (tier_order[pl['tier']], rank_order[pl['rank']], -pl['wr']))

    return sortedPlayers


async def performance(players):
    players_output = []
    SkillFactor_set = {"default": 0.0, "iron": 1.0, "bronze": 1.05, "silver": 1.10, "gold": 1.15, "platinum": 1.20,
                       "emerald": 1.25, "diamond": 1.30, "master": 1.35, "grandmaster": 1.40, "challenger": 1.45}

    for player in players:
        playerPerformanceOfRole = {}
        player_role = player["role"]
        # get player skill factor based on their tier
        player_skillFactor = SkillFactor_set.get(player["tier"])

        # to calculate the relative performance of each player based on their tier and role_preference
        totalPlayerRolesProcessd = 0
        for i, role in enumerate(player_role):
            pref_penality = i * 5

            relative_performance = player_skillFactor * 0.75 + (1 - pref_penality / 100) * 0.25
            playerPerformanceOfRole[role] = relative_performance
            totalPlayerRolesProcessd += 1

        if (totalPlayerRolesProcessd < 5):
            playerPerformanceOfRole['forced'] = player_skillFactor * 0.75

        player["roleBasedPerformance"] = playerPerformanceOfRole

        players_output.append(player)
    return players_output


def teamPerformance(team):
    totalRelativePerformance = 0
    for player in team:
        totalRelativePerformance += sum(player["roleBasedPerformance"].values())
    return totalRelativePerformance


def decode_chromosome(chromosome, players, team_size=5):
    team1 = [players[i] for i in chromosome[:team_size]]
    team2 = [players[i] for i in chromosome[team_size:]]
    return team1, team2


def calculate_fitness(chromosome, players, team_size=5):
    team1, team2 = decode_chromosome(chromosome, players, team_size)
    performance1 = teamPerformance(team1)
    performance2 = teamPerformance(team2)
    diff = abs(performance1 - performance2)
    # Return negative difference: higher fitness means more balanced teams.
    return -diff


def tournament_selection(population, fitnesses, tournament_size=3):
    selected = random.sample(list(zip(population, fitnesses)), tournament_size)
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected[0][0]


def order_crossover(parent1, parent2):
    """
    Order crossover (OX) for permutations.
    """
    size = len(parent1)
    child = [None] * size
    start, end = sorted(random.sample(range(size), 2))
    # Copy a slice from parent1
    child[start:end + 1] = parent1[start:end + 1]
    # Fill the remaining positions with genes from parent2 in order
    fill_values = [gene for gene in parent2 if gene not in child]
    pointer = 0
    for i in range(size):
        if child[i] is None:
            child[i] = fill_values[pointer]
            pointer += 1
    return child


def swap_mutation(chromosome, mutation_rate=0.1):
    """We can adjust the mutation rate at which genes are swapped"""
    new_chromosome = chromosome[:]
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(chromosome)), 2)
        new_chromosome[i], new_chromosome[j] = new_chromosome[j], new_chromosome[i]
    return new_chromosome


def genetic_algorithm(players, population_size=50, generations=100, team_size=5):
    """
    Main GA loop.
    Each chromosome is a permutation of player indices.
    The chromosome is decoded into two teams, and the fitness is the negative absolute difference
    in team performance (i.e., the smaller the difference, the better).
    """
    n = len(players)
    base = list(range(n))
    # Generate initial population: random permutations of player indices.
    population = [random.sample(base, n) for _ in range(population_size)]
    best_chromosome = None
    best_fitness = float('-inf')
    for gen in range(generations):
        fitnesses = [calculate_fitness(chrom, players, team_size) for chrom in population]
        # Update best solution found
        for chrom, fit in zip(population, fitnesses):
            if fit > best_fitness:
                best_fitness = fit
                best_chromosome = chrom[:]
        new_population = []
        for _ in range(population_size):
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)
            child = order_crossover(parent1, parent2)
            child = swap_mutation(child)
            new_population.append(child)
        population = new_population
        print(f"Generation {gen}: Best Fitness = {best_fitness}")
    return best_chromosome, best_fitness


orginal_players = [
    {'user_id': 'player1', 'tier': 'platinum', 'rank': 'II', 'wr': 56, 'role': ['mid', 'top', 'Jungle']},
    {'user_id': 'player2', 'tier': 'gold', 'rank': 'II', 'role': ['support', 'mid'], 'wr': 73},
    {'user_id': 'player3', 'tier': 'platinum', 'rank': 'IV', 'wr': 77,
     'role': ['bottom', 'top', 'Jungle', 'mid', 'support']},
    {'user_id': 'player4', 'tier': 'bronze', 'rank': 'III', 'wr': 78, 'role': ['Jungle']},
    {'user_id': 'player5', 'tier': 'gold', 'rank': 'I', 'wr': 69, 'role': ['top', 'Jungle', 'mid']},
    {'user_id': 'player6', 'tier': 'bronze', 'rank': 'I', 'wr': 86, 'role': ['top', 'Jungle']},
    {'user_id': 'player7', 'tier': 'gold', 'rank': 'IV', 'wr': 47,
     'role': ['bottom', 'mid', 'top', 'Jungle', 'support']},
    {'user_id': 'player8', 'tier': 'platinum', 'rank': 'V', 'wr': 47, 'role': ['mid']},
    {'user_id': 'player9', 'tier': 'diamond', 'rank': 'II', 'wr': 75, 'role': ['mid', 'top', 'Jungle']},
    {'user_id': 'player10', 'tier': 'master', 'rank': 'II', 'wr': 93, 'role': ['top', 'Bottom', 'Jungle', 'support']}
]


async def main():
    # First, sort the players and compute their role-based performance.
    sorted_players = await intialSortingPlayer(orginal_players)
    processed_players = await performance(sorted_players)

    # Run the genetic algorithm.
    # Here, we assume two teams of 5 players each.
    best_chrom, best_fit = genetic_algorithm(processed_players, population_size=100, generations=200, team_size=5)

    # Decode the best chromosome into two teams.
    team1, team2 = decode_chromosome(best_chrom, processed_players, team_size=5)
    print("\n--- Final Teams ---")
    print("Team 1:")
    for p in team1:
        print(p['user_id'], p["roleBasedPerformance"])
    print("\nTeam 2:")
    for p in team2:
        print(p['user_id'], p["roleBasedPerformance"])
    print("\nBest Fitness (balance):", best_fit)


# Run the main function
asyncio.run(main())
