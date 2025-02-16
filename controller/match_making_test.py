import match_making
import genetic_match_making
import asyncio
from genetic_match_making import main as genetic_main
from match_making import main as normal_main

from colorama import init, Fore, Style
init(autoreset=True)


async def main():
    print(Fore.CYAN + Style.BRIGHT + "==== Genetic Matchmaking Output ====")
    await genetic_main()  # Calls the main function from genetic_match_making.py

    print(Fore.MAGENTA + Style.BRIGHT + "\n==== Normal Matchmaking Output ====")
    await normal_main()  # Calls the main function from match_making.py


if __name__ == '__main__':
    asyncio.run(main())
