import asyncio
import random
import json
from model.dbc_model import Tournament_DB, Game, Player
from config import settings
import logging

logger = settings.logging.getLogger("discord")

class GeneticMatchMaking:
    def __init__(self):
        self.db = Tournament_DB()
        self.game_db = Game(db_name=settings.DATABASE_NAME)
        self.player_db = Player(db_name=settings.DATABASE_NAME)
        self.tier_order = {"challenger": 1, "grandmaster": 2, "master": 3, "diamond": 4, "emerald": 5, "platinum": 6, 
                          "gold": 7, "silver": 8, "bronze": 9, "iron": 10, "default": 11}
        self.rank_order = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        self.skill_factor_set = {"default": 0.0, "iron": 1.0, "bronze": 1.05, "silver": 1.10, "gold": 1.15, 
                                "platinum": 1.20, "emerald": 1.25, "diamond": 1.30, "master": 1.35, 
                                "grandmaster": 1.40, "challenger": 1.45}

    async def fetch_player_data(self):
        """Fetch player data from database or combined_player_data.json"""
        try:
            # First, try to get data from database
            players = []
            player_records = self.player_db.get_all_player()
            
            if player_records:
                for player_record in player_records:
                    user_id, game_name, tag_id = player_record
                    
                    # Query the Game table to get game-specific data
                    query = """
                        SELECT tier, rank, role, wins, losses, wr 
                        FROM game 
                        WHERE user_id = ? 
                        ORDER BY game_date DESC 
                        LIMIT 1
                    """
                    try:
                        self.game_db.cursor.execute(query, (user_id,))
                        game_data = self.game_db.cursor.fetchone()
                        
                        if game_data:
                            tier, rank, role_json, wins, losses, wr = game_data
                            
                            # Parse the role JSON string
                            try:
                                role = json.loads(role_json) if role_json else []
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON for role: {role_json}")
                                role = []
                                
                            player = {
                                'user_id': user_id,
                                'game_name': game_name,
                                'tier': tier.lower() if tier else 'default',
                                'rank': rank if rank else 'V',
                                'role': role,
                                'wr': float(wr) * 100 if wr is not None else 50.0  # Convert to percentage
                            }
                            players.append(player)
                    except Exception as ex:
                        logger.error(f"Error fetching game data for user {user_id}: {ex}")
            
            # If database is empty or had errors, use the JSON file
            if not players:
                logger.info("No players found in database, using combined_player_data.json")
                return await self.load_players_from_json()
                
            return players
        except Exception as ex:
            logger.error(f"Error fetching player data: {ex}")
            # Fall back to JSON file
            return await self.load_players_from_json()
    
    async def load_players_from_json(self, count=10):
        """Load players from the combined_player_data.json file"""
        try:
            # Import the function from match_making.py
            from controller.match_making import get_random_players
            
            # Get random players with calculated tiers
            return get_random_players(count=count)
        except Exception as ex:
            logger.error(f"Error loading players from JSON: {ex}")
            return []
            
    async def calculate_player_tier(self, player):
        """Calculate the player's tier rating based on rank"""
        try:
            # Import the calculation function from match_making.py
            from controller.match_making import calculate_player_tier
            
            if 'calculated_tier' not in player and 'tier' in player:
                player['calculated_tier'] = calculate_player_tier(player['tier'])
                
            return player
        except Exception as ex:
            logger.error(f"Error calculating player tier: {ex}")
            return player

    async def initial_sorting_player(self, players):
        """Sort players based on tier, rank, and win ratio"""
        if not players:
            return []
            
        sorted_players = sorted(players, key=lambda pl: (
            self.tier_order.get(pl.get('tier', 'default').lower(), 11),
            self.rank_order.get(pl.get('rank', 'V'), 5),
            -pl.get('wr', 0)
        ))
        
        return sorted_players

    async def calculate_performance(self, players):
        """Calculate performance metrics for each player based on role preferences and calculated tier"""
        players_output = []
        
        for player in players:
            player_performance_of_role = {}
            player_role = player.get("role", [])
            
            # Calculate tier if it's not already calculated
            if 'calculated_tier' not in player:
                player = await self.calculate_player_tier(player)
            
            # Priority order for skill factor calculation:
            # 1. Use manual_tier if available (from database)
            # 2. Use calculated_tier if available (calculated on the fly)
            # 3. Fall back to tier-based skill factor from skill_factor_set
            
            if "manual_tier" in player and player["manual_tier"] is not None:
                # Scale manual_tier (0-10) to match skill_factor_set range (1.0-1.45)
                # This gives a smooth progression where each point in manual_tier
                # roughly equals a 4.5% increase in skill factor
                player_skill_factor = 1.0 + (player["manual_tier"] / 10.0) * 0.45
            elif "calculated_tier" in player:
                # Scale the calculated tier to match our skill_factor_set range
                # Scale from 1-6 range to match our skill_factor_set values (roughly 1.0-1.45)
                player_skill_factor = 1.0 + (player["calculated_tier"] - 1) * 0.09
            else:
                # Fall back to tier-based skill factor
                player_tier = player.get("tier", "default").lower()
                player_skill_factor = self.skill_factor_set.get(player_tier, self.skill_factor_set["default"])
            
            # Calculate relative performance for each role preference
            total_player_roles_processed = 0
            for i, role in enumerate(player_role):
                pref_penalty = i * 5
                relative_performance = player_skill_factor * 0.75 + (1 - pref_penalty / 100) * 0.25
                player_performance_of_role[role] = relative_performance
                total_player_roles_processed += 1
            
            # Add forced role if player doesn't have all 5 roles specified
            if total_player_roles_processed < 5:
                player_performance_of_role['forced'] = player_skill_factor * 0.75
            
            player["roleBasedPerformance"] = player_performance_of_role
            players_output.append(player)
            
        return players_output

    def team_performance(self, team):
        """Calculate total performance of a team"""
        total_relative_performance = 0
        for player in team:
            if "roleBasedPerformance" in player:
                total_relative_performance += sum(player["roleBasedPerformance"].values())
        return total_relative_performance

    def decode_chromosome(self, chromosome, players, team_size=5):
        """Convert a chromosome (list of indices) into two teams"""
        team1 = [players[i] for i in chromosome[:team_size]]
        team2 = [players[i] for i in chromosome[team_size:]]
        return team1, team2

    def calculate_fitness(self, chromosome, players, team_size=5):
        """Calculate fitness of a chromosome (balance between teams)"""
        team1, team2 = self.decode_chromosome(chromosome, players, team_size)
        performance1 = self.team_performance(team1)
        performance2 = self.team_performance(team2)
        diff = abs(performance1 - performance2)
        # Return negative difference: higher fitness means more balanced teams
        return -diff

    def tournament_selection(self, population, fitnesses, tournament_size=3):
        """Select a chromosome using tournament selection"""
        selected = random.sample(list(zip(population, fitnesses)), tournament_size)
        selected.sort(key=lambda x: x[1], reverse=True)
        return selected[0][0]

    def order_crossover(self, parent1, parent2):
        """Order crossover (OX) for permutations"""
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

    def swap_mutation(self, chromosome, mutation_rate=0.1):
        """Swap mutation for permutations"""
        new_chromosome = chromosome[:]
        if random.random() < mutation_rate:
            i, j = random.sample(range(len(chromosome)), 2)
            new_chromosome[i], new_chromosome[j] = new_chromosome[j], new_chromosome[i]
        return new_chromosome

    def genetic_algorithm(self, players, population_size=50, generations=100, team_size=5):
        """Main genetic algorithm loop"""
        if not players or len(players) < team_size * 2:
            logger.error(f"Not enough players for matchmaking. Need {team_size * 2}, have {len(players)}")
            return None, float('-inf')
            
        n = len(players)
        base = list(range(n))
        # Generate initial population: random permutations of player indices
        population = [random.sample(base, n) for _ in range(population_size)]
        best_chromosome = None
        best_fitness = float('-inf')
        
        for gen in range(generations):
            fitnesses = [self.calculate_fitness(chrom, players, team_size) for chrom in population]
            # Update best solution found
            for chrom, fit in zip(population, fitnesses):
                if fit > best_fitness:
                    best_fitness = fit
                    best_chromosome = chrom[:]
            
            # Create new population
            new_population = []
            for _ in range(population_size):
                parent1 = self.tournament_selection(population, fitnesses)
                parent2 = self.tournament_selection(population, fitnesses)
                child = self.order_crossover(parent1, parent2)
                child = self.swap_mutation(child)
                new_population.append(child)
            
            population = new_population
            logger.info(f"Generation {gen}: Best Fitness = {best_fitness}")
            
        return best_chromosome, best_fitness

    async def save_matchmaking_results(self, team1, team2):
        """Save the matchmaking results to the database"""
        try:
            # For future implementation: save teams to a new table or update Matches table
            # This method can be expanded when you decide how to store match data
            team_id = f"match_{int(asyncio.get_event_loop().time())}"
            
            # Example of how you might save to Matches table
            for player in team1:
                user_id = player.get('user_id')
                if user_id:
                    query = """
                        INSERT INTO Matches(user_id, teamUp, teamId) 
                        VALUES(?, ?, ?)
                    """
                    self.db.cursor.execute(query, (user_id, "team1", team_id))
            
            for player in team2:
                user_id = player.get('user_id')
                if user_id:
                    query = """
                        INSERT INTO Matches(user_id, teamUp, teamId) 
                        VALUES(?, ?, ?)
                    """
                    self.db.cursor.execute(query, (user_id, "team2", team_id))
                    
            self.db.connection.commit()
            logger.info(f"Saved matchmaking results with team ID: {team_id}")
            return team_id
        except Exception as ex:
            logger.error(f"Error saving matchmaking results: {ex}")
            return None

    async def run_matchmaking(self, population_size=100, generations=200, team_size=5):
        """Run the entire matchmaking process"""
        # Fetch player data from database or JSON file
        players = await self.fetch_player_data()
        if not players or len(players) < team_size * 2:
            logger.error(f"Not enough players for matchmaking. Need {team_size * 2}, have {len(players)}")
            return None, None
        
        # Calculate tier for each player if not already present
        for i, player in enumerate(players):
            if 'calculated_tier' not in player:
                players[i] = await self.calculate_player_tier(player)
            
        # Sort and process players
        sorted_players = await self.initial_sorting_player(players)
        processed_players = await self.calculate_performance(sorted_players)
        
        # Run the genetic algorithm
        best_chrom, best_fit = self.genetic_algorithm(
            processed_players, 
            population_size=population_size, 
            generations=generations, 
            team_size=team_size
        )
        
        if best_chrom is None:
            return None, None
            
        # Decode the best chromosome into two teams
        team1, team2 = self.decode_chromosome(best_chrom, processed_players, team_size=team_size)
        
        # Calculate and log the team balance
        team1_perf = self.team_performance(team1)
        team2_perf = self.team_performance(team2)
        balance_diff = abs(team1_perf - team2_perf)
        logger.info(f"Team balance: {balance_diff:.2f} difference")
        
        # Save results to database if needed
        # await self.save_matchmaking_results(team1, team2)
        
        return team1, team2


# Test data (used when database integration isn't available)
test_players = [
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
    """Test function to demonstrate matchmaking"""
    matchmaker = GeneticMatchMaking()
    
    # Try to fetch from database first
    players = await matchmaker.fetch_player_data()
    
    # Use test data if no players could be loaded
    if not players:
        logger.warning("Could not load any players, using test data")
        players = test_players
    
    # Display player information
    print("\n=== Using Real Player Data with Tier Assignment ===")
    print("\nPlayers:")
    for player in players:
        # Ensure tier is calculated if it doesn't exist
        if 'calculated_tier' not in player:
            player = await matchmaker.calculate_player_tier(player)
        
        tier_display = f"({player.get('calculated_tier', 'N/A'):.2f})" if 'calculated_tier' in player else ""
        print(f"{player.get('game_name', player.get('user_id'))}: {player.get('tier')} {tier_display}")
    
    # Run the matchmaking process
    team1, team2 = await matchmaker.run_matchmaking(
        population_size=100, 
        generations=200, 
        team_size=5 if len(players) >= 10 else len(players) // 2
    )
    
    if team1 and team2:
        # Output results
        print("\n--- Final Teams ---")
        print("Team 1:")
        for p in team1:
            tier_info = f"Tier: {p.get('calculated_tier', 'N/A'):.2f}" if 'calculated_tier' in p else ""
            print(f"{p.get('game_name', p.get('user_id'))}: {p.get('tier')} {p.get('rank')}, {tier_info}, Roles: {p.get('role')}")
        
        print("\nTeam 2:")
        for p in team2:
            tier_info = f"Tier: {p.get('calculated_tier', 'N/A'):.2f}" if 'calculated_tier' in p else ""
            print(f"{p.get('game_name', p.get('user_id'))}: {p.get('tier')} {p.get('rank')}, {tier_info}, Roles: {p.get('role')}")
        
        # Calculate and display team balance metrics
        team1_perf = matchmaker.team_performance(team1)
        team2_perf = matchmaker.team_performance(team2)
        print(f"\nTeam 1 Performance: {team1_perf:.2f}")
        print(f"Team 2 Performance: {team2_perf:.2f}")
        print(f"Performance Difference: {abs(team1_perf - team2_perf):.2f}")
    else:
        print("Failed to create balanced teams. Not enough players or algorithm failed.")



if __name__ == "__main__":
    asyncio.run(main())


async def setup(bot):

    pass
