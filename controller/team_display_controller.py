import discord
import json
import re
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB

logger = settings.logging.getLogger("discord")

class MatchSelectorView(discord.ui.View):
    """View with a dropdown to select a match ID"""
    
    def __init__(self, controller, announcement_channel, match_ids, timeout=60):
        super().__init__(timeout=timeout)
        self.controller = controller
        self.announcement_channel = announcement_channel
        
        # Create select menu with match options
        select = discord.ui.Select(
            placeholder="Select a match to announce...",
            min_values=1,
            max_values=1,
        )
        
        # Sort match_ids naturally (match_1, match_2, ..., match_10, etc.)
        sorted_match_ids = sorted(match_ids, key=lambda x: int(re.search(r'match_(\d+)', x).group(1)) if re.search(r'match_(\d+)', x) else 0)
        
        # Add options to the select menu
        for match_id in sorted_match_ids[:25]:  # Discord has a 25-option limit
            select.add_option(label=match_id, value=match_id)
        
        # Add callback
        select.callback = self.select_callback
        
        # Add select to view
        self.add_item(select)
    
    async def select_callback(self, interaction):
        """Callback when a match is selected from the dropdown"""
        # Get selected match ID
        match_id = interaction.data['values'][0]
        
        # Pass to controller to handle the announcement
        await self.controller.announce_selected_match(
            interaction, 
            match_id, 
            self.announcement_channel
        )
        
        # Stop listening for interactions
        self.stop()

class TeamDisplayController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="display_teams", description="Display the current teams for a specific match")
    @app_commands.describe(match_id="The ID of the match to display (e.g. match_1)")
    async def display_teams(self, interaction: discord.Interaction, match_id: str):
        """
        Admin command to display the current teams for a specific match
        """
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)
            
            try:
                # Get team data from the database
                db = Tournament_DB()
                
                # Check if match_id exists
                db.cursor.execute(
                    "SELECT COUNT(*) FROM Matches WHERE teamId = ?",
                    (match_id,)
                )
                match_count = db.cursor.fetchone()[0]
                
                if match_count == 0:
                    await interaction.followup.send(f"Match ID '{match_id}' not found.")
                    db.close_db()
                    return
                
                # Get team 1 players
                db.cursor.execute("""
                    SELECT m.user_id, p.game_name, g.tier, g.rank, g.role, g.manual_tier
                    FROM Matches m
                    JOIN player p ON m.user_id = p.user_id
                    LEFT JOIN (
                        SELECT user_id, tier, rank, role, manual_tier, MAX(game_date) as max_date
                        FROM game
                        GROUP BY user_id
                    ) g ON m.user_id = g.user_id
                    WHERE m.teamId = ? AND m.teamUp = 'team1'
                """, (match_id,))
                
                team1_players = []
                for record in db.cursor.fetchall():
                    user_id, game_name, tier, rank, role_json, manual_tier = record
                    
                    # Parse role preferences
                    roles = []
                    if role_json:
                        try:
                            roles = json.loads(role_json)
                            if not isinstance(roles, list):
                                roles = [str(roles)]
                        except:
                            roles = [str(role_json)]
                    
                    player = {
                        'user_id': user_id,
                        'game_name': game_name,
                        'tier': tier.lower() if tier else 'default',
                        'rank': rank if rank else '',
                        'role': roles,
                        'manual_tier': manual_tier
                    }
                    team1_players.append(player)
                
                # Get team 2 players
                db.cursor.execute("""
                    SELECT m.user_id, p.game_name, g.tier, g.rank, g.role, g.manual_tier
                    FROM Matches m
                    JOIN player p ON m.user_id = p.user_id
                    LEFT JOIN (
                        SELECT user_id, tier, rank, role, manual_tier, MAX(game_date) as max_date
                        FROM game
                        GROUP BY user_id
                    ) g ON m.user_id = g.user_id
                    WHERE m.teamId = ? AND m.teamUp = 'team2'
                """, (match_id,))
                
                team2_players = []
                for record in db.cursor.fetchall():
                    user_id, game_name, tier, rank, role_json, manual_tier = record
                    
                    # Parse role preferences
                    roles = []
                    if role_json:
                        try:
                            roles = json.loads(role_json)
                            if not isinstance(roles, list):
                                roles = [str(roles)]
                        except:
                            roles = [str(role_json)]
                    
                    player = {
                        'user_id': user_id,
                        'game_name': game_name,
                        'tier': tier.lower() if tier else 'default',
                        'rank': rank if rank else '',
                        'role': roles,
                        'manual_tier': manual_tier
                    }
                    team2_players.append(player)
                
                db.close_db()
                
                if not team1_players and not team2_players:
                    await interaction.followup.send(
                        f"Match '{match_id}' doesn't have any players. Perhaps it was deleted or not correctly created."
                    )
                    return
                
                # Create embeds for the teams
                team_embeds = self.create_team_embeds(match_id, team1_players, team2_players)
                
                # Create role matchup comparison
                role_matchup_text = self.create_role_matchup_text(team1_players, team2_players)
                
                # Send the team display
                await interaction.followup.send(
                    content=f"**Teams for Match ID: `{match_id}`**\n\n{role_matchup_text}",
                    embeds=team_embeds
                )
                
            except Exception as ex:
                logger.error(f"Error in display_teams: {ex}")
                await interaction.followup.send(f"Error displaying teams: {str(ex)}")
                
        else:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
    
    @app_commands.command(name="announce_teams", description="Announce teams to a channel using a dropdown")
    @app_commands.describe(
        channel="The channel to announce to (defaults to tournament announcement channel)"
    )
    async def announce_teams(
        self, 
        interaction: discord.Interaction,
        channel: discord.TextChannel = None
    ):
        """
        Admin command to announce teams to a channel using a dropdown to select the match
        """
        if interaction.user.guild_permissions.administrator:
            try:
                # Determine the channel to send to
                announcement_channel = channel
                if announcement_channel is None:
                    # Try to get the tournament announcement channel from settings
                    tournament_ch_id = settings.TOURNAMENT_CH
                    
                    # Log the value for debugging
                    logger.info(f"TOURNAMENT_CH value: {tournament_ch_id}")
                    
                    # Try different possible formats of the channel ID
                    if tournament_ch_id:
                        # Try direct channel ID (numeric)
                        if tournament_ch_id.isdigit():
                            announcement_channel = self.bot.get_channel(int(tournament_ch_id))
                            if announcement_channel:
                                logger.info(f"Found channel by ID: {announcement_channel.name}")
                        
                        # Try channel name format
                        elif tournament_ch_id.startswith('#'):
                            # Remove the # prefix if present
                            channel_name = tournament_ch_id[1:] 
                            # Look for channel by name
                            for guild in self.bot.guilds:
                                for channel in guild.text_channels:
                                    if channel.name.lower() == channel_name.lower():
                                        announcement_channel = channel
                                        logger.info(f"Found channel by name: {channel.name}")
                                        break
                                if announcement_channel:
                                    break
                        
                        # Try direct channel name without #
                        else:
                            # Look for channel by name
                            for guild in self.bot.guilds:
                                for channel in guild.text_channels:
                                    if channel.name.lower() == tournament_ch_id.lower():
                                        announcement_channel = channel
                                        logger.info(f"Found channel by name: {channel.name}")
                                        break
                                if announcement_channel:
                                    break
                
                if announcement_channel is None:
                    await interaction.response.send_message(
                        "Could not find announcement channel. Please specify a channel or set TOURNAMENT_CH in settings.",
                        ephemeral=True
                    )
                    return
                
                # Get active match IDs from the database
                db = Tournament_DB()
                
                db.cursor.execute("""
                    SELECT DISTINCT teamId 
                    FROM Matches 
                    WHERE teamId LIKE 'match_%'
                    ORDER BY teamId
                """)
                match_ids = [record[0] for record in db.cursor.fetchall()]
                db.close_db()
                
                if not match_ids:
                    await interaction.response.send_message(
                        "No active matches found. Create teams first using `/run_matchmaking`.",
                        ephemeral=True
                    )
                    return
                
                # Create select menu for match selection
                view = MatchSelectorView(self, announcement_channel, match_ids)
                
                # Send message with dropdown
                await interaction.response.send_message(
                    f"Select a match to announce to {announcement_channel.mention}:",
                    view=view,
                    ephemeral=True
                )
                
            except Exception as ex:
                logger.error(f"Error in announce_teams: {ex}")
                await interaction.response.send_message(
                    f"Error getting match data: {str(ex)}",
                    ephemeral=True
                )
                
        else:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
    
    async def announce_selected_match(self, interaction, match_id, announcement_channel):
        """
        Announce the selected match to the specified channel
        Called by the MatchSelectorView when a match is selected
        """
        await interaction.response.defer(thinking=True)
        
        try:
            # Get team data from the database
            db = Tournament_DB()
            
            # Check if match_id exists
            db.cursor.execute(
                "SELECT COUNT(*) FROM Matches WHERE teamId = ?",
                (match_id,)
            )
            match_count = db.cursor.fetchone()[0]
            
            if match_count == 0:
                await interaction.followup.send(f"Match ID '{match_id}' not found.")
                db.close_db()
                return
            
            # Get team 1 players
            db.cursor.execute("""
                SELECT m.user_id, p.game_name, g.tier, g.rank, g.role
                FROM Matches m
                JOIN player p ON m.user_id = p.user_id
                LEFT JOIN (
                    SELECT user_id, tier, rank, role, MAX(game_date) as max_date
                    FROM game
                    GROUP BY user_id
                ) g ON m.user_id = g.user_id
                WHERE m.teamId = ? AND m.teamUp = 'team1'
            """, (match_id,))
            
            team1_players = []
            team1_user_ids = []
            for record in db.cursor.fetchall():
                user_id, game_name, tier, rank, role_json = record
                team1_user_ids.append(user_id)
                
                # Parse role preferences
                roles = []
                if role_json:
                    try:
                        roles = json.loads(role_json)
                        if not isinstance(roles, list):
                            roles = [str(roles)]
                    except:
                        roles = [str(role_json)]
                
                player = {
                    'user_id': user_id,
                    'game_name': game_name,
                    'tier': tier.lower() if tier else 'default',
                    'rank': rank if rank else '',
                    'role': roles
                }
                team1_players.append(player)
            
            # Get team 2 players
            db.cursor.execute("""
                SELECT m.user_id, p.game_name, g.tier, g.rank, g.role
                FROM Matches m
                JOIN player p ON m.user_id = p.user_id
                LEFT JOIN (
                    SELECT user_id, tier, rank, role, MAX(game_date) as max_date
                    FROM game
                    GROUP BY user_id
                ) g ON m.user_id = g.user_id
                WHERE m.teamId = ? AND m.teamUp = 'team2'
            """, (match_id,))
            
            team2_players = []
            team2_user_ids = []
            for record in db.cursor.fetchall():
                user_id, game_name, tier, rank, role_json = record
                team2_user_ids.append(user_id)
                
                # Parse role preferences
                roles = []
                if role_json:
                    try:
                        roles = json.loads(role_json)
                        if not isinstance(roles, list):
                            roles = [str(roles)]
                    except:
                        roles = [str(role_json)]
                
                player = {
                    'user_id': user_id,
                    'game_name': game_name,
                    'tier': tier.lower() if tier else 'default',
                    'rank': rank if rank else '',
                    'role': roles
                }
                team2_players.append(player)
            
            db.close_db()
            
            if not team1_players and not team2_players:
                await interaction.followup.send(
                    f"Match '{match_id}' doesn't have any players. Perhaps it was deleted or not correctly created."
                )
                return
            
            # Create embeds for the teams
            team_embeds = self.create_team_embeds(match_id, team1_players, team2_players)
            
            # Create role matchup comparison
            role_matchup_text = self.create_role_matchup_text(team1_players, team2_players)
            
            # Create a mention string for all players
            mentions = []
            guild = interaction.guild
            if guild:
                for user_id in team1_user_ids + team2_user_ids:
                    try:
                        member = await guild.fetch_member(int(user_id))
                        if member:
                            mentions.append(member.mention)
                    except:
                        pass
            
            mentions_str = " ".join(mentions) if mentions else ""
            
            # Send the announcement
            announcement_message = f"**🏆 Team Announcement for Match: `{match_id}` 🏆**\n\n"
            if mentions:
                announcement_message += f"Players: {mentions_str}\n\n"
            
            announcement_message += role_matchup_text
            
            await announcement_channel.send(
                content=announcement_message,
                embeds=team_embeds
            )
            
            await interaction.followup.send(
                f"Teams for Match ID '{match_id}' have been announced in {announcement_channel.mention}."
            )
            
        except Exception as ex:
            logger.error(f"Error in announce_selected_match: {ex}")
            await interaction.followup.send(f"Error announcing teams: {str(ex)}")
    
    def create_team_embeds(self, match_id, team1_players, team2_players):
        """
        Create Discord embeds for team displays
        
        Args:
            match_id: The match ID
            team1_players: List of player dictionaries for team 1
            team2_players: List of player dictionaries for team 2
            
        Returns:
            list: List of embeds for team 1 and team 2
        """
        # Role color mapping (using League of Legends colors)
        role_colors = {
            "top": "🟥",      # Red
            "jungle": "🟩",   # Green
            "mid": "🟨",      # Yellow
            "bottom": "🟦",   # Blue
            "support": "🟪",  # Purple
            "tbd": "⬜",      # White/empty
            "forced": "⬛"     # Black/forced
        }
        
        # Determine roles for each player
        # We need to replicate the role assignment logic since we don't have access to the assigned_role values
        from controller.genetic_match_making import GeneticMatchMaking
        matchmaker = GeneticMatchMaking()
        
        # Assign roles if we have enough players
        standard_roles = ["top", "jungle", "mid", "bottom", "support"]
        if len(team1_players) >= 5:
            team1_players = matchmaker.assign_team_roles(team1_players)
        if len(team2_players) >= 5:
            team2_players = matchmaker.assign_team_roles(team2_players)
        
        # Create team 1 embed
        team1_embed = discord.Embed(
            title=f"Team 1 (Match ID: {match_id})",
            color=discord.Color.blue()
        )
        
        # Add team 1 players
        for i, player in enumerate(team1_players):
            name = player.get('game_name', player.get('user_id', 'Unknown'))
            tier = player.get('tier', 'unknown').capitalize()
            rank = player.get('rank', '')
            roles = player.get('role', [])
            
            # Format roles with colors
            colored_roles = []
            for role in roles:
                role_lower = role.lower()
                role_emoji = role_colors.get(role_lower, "⬜")
                colored_roles.append(f"{role_emoji} {role.capitalize()}")
            
            role_str = '  '.join(colored_roles) if colored_roles else 'None'
            
            # Get assigned role if available
            if "assigned_role" in player:
                assigned_role = player["assigned_role"]
            else:
                # Try to find best role based on standard roles
                assigned_role = "TBD"
                for std_role in standard_roles:
                    if std_role in [r.lower() for r in roles]:
                        assigned_role = std_role
                        break
            
            assigned_role_lower = assigned_role.lower()
            assigned_emoji = role_colors.get(assigned_role_lower, role_colors["tbd"])
            colored_assigned = f"{assigned_emoji} {assigned_role.capitalize()}"
            
            team1_embed.add_field(
                name=f"Player {i + 1}: {name}",
                value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}\n**Assigned:** {colored_assigned}",
                inline=True
            )
        
        # Create team 2 embed
        team2_embed = discord.Embed(
            title=f"Team 2 (Match ID: {match_id})",
            color=discord.Color.red()
        )
        
        # Add team 2 players
        for i, player in enumerate(team2_players):
            name = player.get('game_name', player.get('user_id', 'Unknown'))
            tier = player.get('tier', 'unknown').capitalize()
            rank = player.get('rank', '')
            roles = player.get('role', [])
            
            # Format roles with colors
            colored_roles = []
            for role in roles:
                role_lower = role.lower()
                role_emoji = role_colors.get(role_lower, "⬜")
                colored_roles.append(f"{role_emoji} {role.capitalize()}")
            
            role_str = '  '.join(colored_roles) if colored_roles else 'None'
            
            # Get assigned role if available
            if "assigned_role" in player:
                assigned_role = player["assigned_role"]
            else:
                # Try to find best role based on standard roles
                assigned_role = "TBD"
                for std_role in standard_roles:
                    if std_role in [r.lower() for r in roles]:
                        assigned_role = std_role
                        break
            
            assigned_role_lower = assigned_role.lower()
            assigned_emoji = role_colors.get(assigned_role_lower, role_colors["tbd"])
            colored_assigned = f"{assigned_emoji} {assigned_role.capitalize()}"
            
            team2_embed.add_field(
                name=f"Player {i + 1}: {name}",
                value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}\n**Assigned:** {colored_assigned}",
                inline=True
            )
        
        return [team1_embed, team2_embed]
    
    def create_role_matchup_text(self, team1_players, team2_players):
        """
        Create text showing role matchups between teams
        
        Args:
            team1_players: List of player dictionaries for team 1
            team2_players: List of player dictionaries for team 2
            
        Returns:
            str: Formatted role matchup text
        """
        # Make sure roles are assigned
        from controller.genetic_match_making import GeneticMatchMaking
        matchmaker = GeneticMatchMaking()
        
        # Assign roles if we have enough players
        if len(team1_players) >= 5:
            team1_players = matchmaker.assign_team_roles(team1_players)
        if len(team2_players) >= 5:
            team2_players = matchmaker.assign_team_roles(team2_players)
        
        # Get role emoji mapping
        role_emoji_map = {
            "top": "🟥 Top",
            "jungle": "🟩 Jungle",
            "mid": "🟨 Mid", 
            "bottom": "🟦 Bottom",
            "support": "🟪 Support"
        }
        
        # Standard roles in League of Legends
        standard_roles = ["top", "jungle", "mid", "bottom", "support"]
        role_matchup_text = "**Role Matchups:**\n"
        
        for role in standard_roles:
            team1_player = next((p for p in team1_players if p.get("assigned_role") == role), None)
            team2_player = next((p for p in team2_players if p.get("assigned_role") == role), None)
            
            if team1_player and team2_player:
                team1_name = team1_player.get('game_name', 'Unknown')
                team2_name = team2_player.get('game_name', 'Unknown')
                team1_tier = team1_player.get('tier', 'default').capitalize()
                team2_tier = team2_player.get('tier', 'default').capitalize()
                team1_rank = team1_player.get('rank', '')
                team2_rank = team2_player.get('rank', '')
                
                role_display = role_emoji_map.get(role, role.capitalize())
                role_matchup_text += f"{role_display}: {team1_name} ({team1_tier} {team1_rank}) vs {team2_name} ({team2_tier} {team2_rank})\n"
        
        return role_matchup_text

async def setup(bot):
    await bot.add_cog(TeamDisplayController(bot))