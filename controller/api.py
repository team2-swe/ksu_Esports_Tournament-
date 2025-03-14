import discord
from discord.ext import commands, tasks
from config import settings
from model.dbc_model import Tournament_DB ,Player, Player_game_info
import requests

logger = settings.logging.getLogger("discord")

'''Depend on the API we use, we can use below two ptions
    Depend on the API we can use API key for request autnetication
    or
    We use API key in headeres for authorization
'''
class ApiCommon:
    @staticmethod
    async def get_player_details(game_name, tag_id):
        # headers = {
        #     'Authorization': f'Bearer {settings.API_KEY}',
        #     'Content-Type': 'application/json'
        #     }
        headers = {'X-Riot-Token': settings.API_KEY}

        url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_id}?api_key={settings.API_KEY}'
        url_puuid = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid"
        url_summonId = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner"
        try: 
            # response = requests.get(url, headers=headers)
            response = requests.get(url=url, headers=headers)

            if response.status_code == 200:
                account_info = response.json()
                puuid = account_info['puuid']

                if puuid is not None:
                    response = requests.get(f"{url_puuid}/{puuid}?api_key={settings.API_KEY}", headers=headers)
                    if response.status_code==200:
                        result_format = response.json()
                        summoner_id = result_format['id']

                        if summoner_id is not None:
                            response = requests.get(f"{url_summonId}/{summoner_id}?api_key={settings.API_KEY}", headers=headers)
                            return response.json()
                    else:
                        logger.info(f"not result for user puuid {puuid} and url: {url_puuid}")
                        return
            else:
                print(f"not result for user tage_id: {tag_id} and url: {url}")

        except Exception as ex:
            logger.info(f"the request to get user puui is failed")

    async def push_player_info(player_id, game_name, tag_id):
        logger.info(f"start to fetch a player discord is: {player_id} details from riot api")
        resultJson = await ApiCommon.get_player_details(game_name, tag_id)
        db = Tournament_DB()
        if resultJson:
            player_tier = resultJson[0]['tier'] if 'tier' in resultJson[0] else 'unranked'
            player_rank = resultJson[0]['rank'] if 'rank' in resultJson[0] else 'unranked'
            player_wins = 0 #resultJson[0]['wins'] if 'wins' in resultJson[0] else 0
            player_losses = 0 #resultJson[0]['losses'] if 'losses' in resultJson[0] else 0
            Player_game_info.update_player_API_info(db, player_id, player_tier, player_rank, player_wins, player_losses)
        else:
            logger.info(f"the player {player_id} is not found in the riot api")
            Player.remove_player(db, player_id)
        
        db.close_db()


class Api_Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_players_details.start()

    def cog_unload(self):
        self.fetch_players_details.cancel()

    @tasks.loop(seconds=7200)
    async def fetch_players_details(self):
        db = Tournament_DB()
        all_players = Player.get_players(db)
        db.close_db()
        if all_players is not None:
            for player in all_players:
                await ApiCommon.push_player_info(player[0], player[1], player[2])


    @fetch_players_details.before_loop
    async def before_fetch_players_details(self):
        await self.bot.wait_until_ready()


    @commands.Cog.listener()
    async def on_message(self, message):
        """this event listener is for admin to stop and run the api schedule
        """
        if message.content.strip().lower() == settings.STOP_API_TASK.strip().lower():
            #check the permission if the user is admin
            if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
                if self.fetch_players_details.is_running():
                    self.fetch_players_details.cancel()
                    await message.channel.send("api task is stopped")

                else:
                    await message.channel.send("api task wasnt running")

        if message.content.strip().lower() == settings.START_API_TASK.strip().lower():
            #check the permission if the user is admin
            if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
                if not self.fetch_players_details.is_running():
                    self.fetch_players_details.start()
                    await message.channel.send("api task start")

                else:
                    await message.channel.send("api task wasnt stoped")


async def setup(bot):
    await bot.add_cog(Api_Collection(bot))