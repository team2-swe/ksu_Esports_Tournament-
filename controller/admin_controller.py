import discord, asyncio
from discord import app_commands
from discord.ext import commands
from view.checkIn_view import CheckinView
from config import settings
from common.cached_details import Details_Cached
from model.player import PlayerModel

logger = settings.logging.getLogger("discord")

class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="Create check-in for a game")
    @app_commands.describe(timeout="Time in seconds before the command message freezes")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        # confirm_result = Player.fetch(interaction)
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            channelName = settings.TOURNAMENT_CH
            channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
            channel = interaction.guild.get_channel(channel_id)
            try:
                logger.info(f"Time out value is: {timeout}")
                game_checkin_view = CheckinView(timeout=timeout)  

                # await interaction.response.send_message("check in instruction: the checkin time is ready")
                # message = await interaction.followup.send(view=signUp_view)
                # signUp_view.message = message

                # await signUp_view.wait()
                message = await channel.send(view=game_checkin_view)
                game_checkin_view.message = message
                game_checkin_view.channel = channel

                await interaction.response.send_message(f"Invitation successfully sent")

                await asyncio.sleep(timeout)
                await message.delete()

                await interaction.response.send_message(f"Check-In time has been completed")
            except discord.Forbidden:
                await channel.send(f"Bot does not have permission to send a message in {channel.name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Sorry you dont have access to use this command",
                                                    ephemeral=True)
            
    # This will add toxicity points to the player the admin chooses
    @app_commands.command(name="toxicity", description="Add 1 point to the players toxicity level")
    @app_commands.describe(player="The player to add toxicity to")
    @app_commands.checks.has_permissions(administrator=True)
    async def toxicity(self, interaction: discord.Interaction, player: str):
    # Check if the player is an admin and end if not
        if interaction.user.guild_permissions.administrator:
            try:
                # Call the method to update the database and check if it returns a success
                found_user = PlayerModel.update_toxicity(interaction, player.lower())
                if found_user:
                    await interaction.response.send_message(f"{player}'s toxicity point has been updated.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{player} could not be found.", ephemeral=True)

            except Exception as e:
                print(f'An error occured: {e}')
        else:
            await interaction.response.send_message("❌ This command is only for administrators.", ephemeral=True)
            return
        
    #Still working on this command but it atleast shows the command in the bot. 
    @app_commands.command(name = 'setplayertier', description = "Set a player's tier to override their calculated tier.")
    async def setplayertier(interaction: discord.Interaction, username: str, tier: int):
        # Admin only command
        if interaction.user.guild_permissions.administrator:      
            try:
                # If the user was passed in using the @Discordname parse the ID
                if "<@" in username:
                    username = username[2:-1]
            
                # Create database connection
                dbconn = sqlite3.connect("bot.db")
                cur = dbconn.cursor()

                # Search for the player by Riot ID or by their Discord Name
                query = f"""
                    SELECT discordName, Tier, tieroverride
                    FROM Player p
                    INNER JOIN vw_Player vp ON vp.discordID = p.discordID
                    WHERE LOWER(discordName) = ? OR LOWER(p.riotID) = ? OR p.discordID = ?
                    """
                cur.execute(query, [username.lower(), username.lower(), username])
                player = cur.fetchone()

                # If the player is not found then return a message
                if player == None:
                    await interaction.response.send_message(f"{username} was not found in the database.", ephemeral=True)
                
                else:
                    # Query to save the change
                    query = """
                        UPDATE PLAYER SET tieroverride = ?
                        WHERE LOWER(discordName) = ? OR LOWER(riotID) = ? OR discordID = ?
                        """
                    cur.execute(query, [tier, username.lower(), username.lower(), username])
                    dbconn.commit()

                    # Create the embed for displaying the change
                    embedTier = discord.Embed(color = discord.Color.green(), title = 'Player Tier: ' + username)
                    embedTier.add_field(name = 'Old override tier', value = player[2], inline=False)
                    embedTier.add_field(name = 'Old calculated tier', value = player[1], inline=False)
                    embedTier.add_field(name = 'New override tier', value = tier, inline=False)

                    # Output the embed
                    await interaction.response.send_message(embed=embedTier, ephemeral=True)
                
            # Catch sql errors, print to console and output message to Discord
            except sqlite3.Error as e:
                print(f"Terminating due to database clear error: {e}")
                await interaction.response.send_message(f"Failed due to database error {e}", ephemeral=True)

            finally:
                cur.close()
                dbconn.close() 
                return
        else:
            await interaction.response.send_message("❌ This command is only for administrators.", ephemeral=True)
            return



async def setup(bot):
    await bot.add_cog(Admin_commands(bot))