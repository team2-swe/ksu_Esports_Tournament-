import asyncio
from controller import match_making
from controller.genetic_match_making import GeneticMatchMaking, main as genetic_main
from controller.match_making import main as normal_main

from colorama import init, Fore, Style
init(autoreset=True)


async def main():
    """Run and compare both matchmaking algorithms"""
    # Run genetic matchmaking
    print(Fore.CYAN + Style.BRIGHT + "==== Genetic Matchmaking Output ====")
    await genetic_main()  # Calls the main function from genetic_match_making.py
    
    # Run normal matchmaking
    print(Fore.MAGENTA + Style.BRIGHT + "\n==== Normal Matchmaking Output ====")
    await normal_main()  # Calls the main function from match_making.py


async def batch_test(iterations=10):
    """Run a batch test comparing the two algorithms multiple times and compare results"""
    genetic_matcher = GeneticMatchMaking()
    genetic_scores = []
    normal_scores = []
    
    print(Fore.YELLOW + Style.BRIGHT + f"Running {iterations} test iterations...")
    
    # Use test data from genetic_match_making.py for consistent comparison
    from controller.genetic_match_making import test_players
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}...")
        
        # Run genetic algorithm
        team1, team2 = await genetic_matcher.run_matchmaking(
            population_size=50,  # Smaller for faster testing
            generations=100,     # Smaller for faster testing
            team_size=5
        )
        
        if team1 and team2:
            team1_perf = genetic_matcher.team_performance(team1)
            team2_perf = genetic_matcher.team_performance(team2)
            genetic_diff = abs(team1_perf - team2_perf)
            genetic_scores.append(genetic_diff)
        
        # Run normal algorithm (you may need to adapt this part)
        sorted_players = await match_making.intialSortingPlayer(test_players)
        processed_players = await match_making.performance(sorted_players)
        t1, t2 = match_making.buildTeams(processed_players)
        
        if t1 and t2:
            # Extract player objects for performance calculation
            team1_players = [item["assigned_to"] for item in t1 if "assigned_to" in item]
            team2_players = [item["assigned_to"] for item in t2 if "assigned_to" in item]
            
            # Calculate team performances
            t1_perf = match_making.teamPerformance(team1_players)
            t2_perf = match_making.teamPerformance(team2_players)
            normal_diff = abs(t1_perf - t2_perf)
            normal_scores.append(normal_diff)
    
    # Calculate and display results
    if genetic_scores and normal_scores:
        genetic_avg = sum(genetic_scores) / len(genetic_scores)
        normal_avg = sum(normal_scores) / len(normal_scores)
        
        print(Fore.GREEN + Style.BRIGHT + "\n==== Test Results ====")
        print(f"Genetic Algorithm - Average Performance Difference: {genetic_avg:.4f}")
        print(f"Normal Algorithm - Average Performance Difference: {normal_avg:.4f}")
        
        improvement = ((normal_avg - genetic_avg) / normal_avg) * 100
        print(f"Improvement: {improvement:.2f}%")
        
        if genetic_avg < normal_avg:
            print(Fore.GREEN + "Genetic algorithm produced more balanced teams on average!")
        elif genetic_avg > normal_avg:
            print(Fore.RED + "Normal algorithm produced more balanced teams on average!")
        else:
            print(Fore.YELLOW + "Both algorithms produced equally balanced teams on average.")
    else:
        print(Fore.RED + "Failed to gather enough data for comparison.")


if __name__ == '__main__':
    # Uncomment the desired test mode
    
    # Regular comparison (single run of each algorithm)
    asyncio.run(main())
    
    # Batch testing for statistical comparison 
    # (uncomment to run multiple iterations and get averages)
    # asyncio.run(batch_test(iterations=5))

# Add the required setup function for Discord.py cog loading
async def setup(bot):
    # This file doesn't need to be a command cog, but Discord.py requires a setup function
    pass
