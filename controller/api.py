import discord
from discord.ext import commands, tasks
from config import settings
from model.dbc_model import Player
import requests

logger = settings.logging.getLogger("discord")

'''Depend on the API we use, we can use below two ptions
    Depend on the API we can use API key for request autnetication
    or
    We use API key in headeres for authorization
'''

class Api_Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_all_players_details.start()

    def cog_unload(self):
        self.fetch_all_players_details.cancel()

    @tasks.loop(seconds=600)
    async def fetch_all_players_details(self):
        all_players = Player.select()
        for player in all_players:
            logger.info(f"start to fetch a player discord is: {player.discord_id} details from riot api")
            player_info = await self.get_player_details(player.game_name, player.tag_id)

            if player_info:
                player_rank = player_info.get('rank', 'unranked')
                player.add_update_player_DB(player.discord_id, player_rank)

    @fetch_all_players_details.before_loop
    async def before_fetch_all_players_details(self):
        await self.bot.wait_until_ready()


    async def get_player_details(interaction: discord.Interaction, game_name, tag_id):
        headers = {
            'Authorization': f'Bearer {settings.API_KEY}',
            'Content-Type': 'application/json'
            }

        url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_id}'
        url_puuid = f'https://na1.api.riotgames.com//lol/summoner/v4/summoners/by-puuid' 
        try: 
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                account_info = response.json()
                puuid = account_info['puuid']

                if puuid is not None:
                    response = requests.get(f"{url_puuid}/{puuid}", headers=headers)
                    if response.status_code==200:
                        return response.json()
                    else:
                        logger.info(f"not result for user puuid {puuid} and url: {url_puuid}")
                        return
            else:
                print(f"not result for user tage_id: {tag_id} and url: {url}")
                return
        except Exception as ex:
            logger.info(f"the request to get user puui is failed")

    @tasks.loop(seconds=300)
    async def fetch_all_players_details(self):
        all_players = Player.select()
        for player in all_players:
            logger.info(f"start to fetch a player discord is: {player.discord_id} details from riot api")
            player_info = Api_Collection.get_player_details(player.game_name, player.tag_id)

            if player_info:
                player_rank = player_info.get('rank', 'unranked')
                player.add_update_player_DB(player.discord_id, player_rank)

    @commands.Cog.listener()
    async def on_message(self, message):
        """this event listner is for admin to stop and run the api schedule
        """
        if message.content.strip().lower() == settings.STOP_API_TASK.strip().lower():
            #check the permission if the user is admin
            if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
                if self.fetch_all_players_details.is_running():
                    self.fetch_all_players_details.cancel()
                    await message.channel.send("api task is stoped", ephemeral=True)

                else:
                    await message.channel.send("api task wasnt running", ephemeral=True)

        if message.content.strip().lower() == settings.START_API_TASK.strip().lower():
            #check the permission if the user is admin
            if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
                if not self.fetch_all_players_details.is_running():
                    self.fetch_all_players_details.start()
                    await message.channel.send("api task start", ephemeral=True)

                else:
                    await message.channel.send("api task was running", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Api_Collection(bot))