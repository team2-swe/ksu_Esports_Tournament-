import discord, asyncio
import random
import json
from discord import app_commands
from discord.ext import commands
from view.checkIn_view import CheckinView
from config import settings
from common.cached_details import Details_Cached
from model.dbc_model import Tournament_DB, Player, Game
from controller.genetic_match_making import GeneticMatchMaking

logger = settings.logging.getLogger("discord")


class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="checking to play next game")
    @app_commands.describe(timeout="time in second befor the command message frez")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        # confirm_result = Player.fetch(interaction)
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            channelName = settings.TOURNAMENT_CH

            # Try to find the channel directly first
            for channel in interaction.guild.channels:
                if channel.name == channelName and isinstance(channel, discord.TextChannel):
                    logger.info(f"Found channel directly: {channel.name} with ID {channel.id}")
                    try:
                        logger.info(f"time out value is {timeout}")
                        game_checkin_view = CheckinView(timeout=timeout)

                        message = await channel.send(view=game_checkin_view)
                        game_checkin_view.message = message
                        game_checkin_view.channel = channel

                        await interaction.response.send_message(f"Invitation successfully sent to {channel.name}")

                        await asyncio.sleep(timeout)
                        await message.delete()

                        return
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            f"Bot doesn't have permission to send a message in {channel.name}", ephemeral=True)
                        return

            # Fallback to cached channel ID if direct search fails
            channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
            if channel_id:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    try:
                        logger.info(f"time out value is {timeout}")
                        game_checkin_view = CheckinView(timeout=timeout)
                        message = await channel.send(view=game_checkin_view)
                        game_checkin_view.message = message
                        game_checkin_view.channel = channel
                        await interaction.response.send_message(f"Invitation successfully sent to {channel.name}")

                        await asyncio.sleep(timeout)
                        await message.delete()

                        return
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            f"Bot doesn't have permission to send a message in {channel.name}", ephemeral=True)
                        return

            # If we get here, we couldn't find the channel
            await interaction.response.send_message(
                f"Could not find channel named '{channelName}'. Available channels: {', '.join([ch.name for ch in interaction.guild.channels if isinstance(ch, discord.TextChannel)])}",
                ephemeral=True)
        else:
            await interaction.response.send_message(f"Sorry you dont have required permission to use this command",
                                                    ephemeral=True)

    @app_commands.command(name="simulate_checkins", description="Simulate League of Legends players checking in")
    @app_commands.describe(player_count="Number of players to simulate")
    async def simulate_checkins(self, interaction: discord.Interaction, player_count: int = 10):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()

            # League of Legends specific data
            lanes = ["top", "jungle", "mid", "bottom", "support"]
            tiers = ["iron", "bronze", "silver", "gold", "platinum", "emerald", "diamond", "master", "grandmaster",
                     "challenger"]
            ranks = ["I", "II", "III", "IV"]

            # Delete existing simulated players to avoid duplicates
            try:
                db.cursor.execute("DELETE FROM player WHERE user_id >= 9000000")
                db.cursor.execute("DELETE FROM game WHERE user_id >= 9000000")
                db.connection.commit()
                logger.info("Cleared previous simulated players")
            except Exception as ex:
                logger.error(f"Error clearing previous players: {ex}")

            player_ids = []
            for i in range(player_count):
                # Generate unique ID for simulated player
                player_id = 9000000 + i
                player_ids.append(player_id)

                # Register player
                summoner_name = f"Summoner{1000 + i}"
                tag_id = f"#{random.randint(1000, 9999)}"

                # Generate random skill data
                tier = random.choice(tiers)
                rank = random.choice(ranks)
                wins = random.randint(10, 200)
                losses = random.randint(10, 200)

                try:
                    # Insert player record
                    insert_query = "INSERT INTO player(user_id, game_name, tag_id) VALUES(?, ?, ?)"
                    db.cursor.execute(insert_query, (player_id, summoner_name, tag_id))

                    # Insert player preferences (1-3 lane preferences)
                    pref_count = random.randint(1, 3)
                    random_lanes = random.sample(lanes, k=pref_count)

                    # Insert skills and preferences
                    game_query = "INSERT INTO game(user_id, game_name, tier, rank, role, wins, losses) VALUES(?, ?, ?, ?, ?, ?, ?)"
                    db.cursor.execute(
                        game_query,
                        (
                            player_id,
                            "League of Legends",
                            tier,
                            rank,
                            json.dumps(random_lanes),
                            wins,
                            losses
                        )
                    )

                except Exception as ex:
                    logger.error(f"Error creating simulated player: {ex}")

            db.connection.commit()
            db.close_db()
            await interaction.response.send_message(
                f"Successfully simulated {player_count} League of Legends players with realistic tiers, ranks, and lane preferences")
        else:
            await interaction.response.send_message(f"Sorry you dont have required permission to use this command",
                                                    ephemeral=True)

    @app_commands.command(name="list_players", description="List all registered players")
    async def list_players(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()
            try:
                # Get all players from database
                all_players = Player.get_all_player(db)

                if not all_players or len(all_players) == 0:
                    await interaction.response.send_message("No players registered yet.")
                    return

                # Create an embed to display players
                embed = discord.Embed(
                    title="League of Legends Players",
                    color=discord.Color.blue(),
                    description=f"Total Players: {len(all_players)}"
                )

                for i, player in enumerate(all_players):
                    user_id, game_name, tag_id = player

                    # Try to get player stats from game table
                    try:
                        db.cursor.execute(
                            "SELECT role, tier, rank, wins, losses, wr FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                            (user_id,)
                        )
                        game_data = db.cursor.fetchone()

                        if game_data:
                            role_data, tier, rank, wins, losses, win_rate = game_data

                            # Parse role preferences
                            role_str = "None"
                            if role_data:
                                try:
                                    roles = json.loads(role_data)
                                    role_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
                                except:
                                    role_str = str(role_data)

                            # Format tier and rank
                            tier_str = tier.capitalize() if tier else "Unranked"
                            rank_str = rank if rank else ""

                            # Calculate win rate if not provided
                            if win_rate is None and wins is not None and losses is not None:
                                total_games = wins + losses
                                if total_games > 0:
                                    win_rate = (wins / total_games) * 100
                                else:
                                    win_rate = 0

                            # Format stats string
                            stats = f"**Rank:** {tier_str} {rank_str}\n"
                            if wins is not None and losses is not None:
                                stats += f"**Record:** {wins}W {losses}L"
                                if win_rate is not None:
                                    stats += f" ({win_rate:.1f}%)"

                            # Add player to embed (up to 15 players per embed)
                            if i < 15:
                                embed.add_field(
                                    name=f"{game_name} {tag_id}",
                                    value=f"{stats}\n**Roles:** {role_str}",
                                    inline=True
                                )
                        else:
                            # Fallback if no game data exists
                            if i < 15:
                                embed.add_field(
                                    name=f"{game_name} {tag_id}",
                                    value="No game data available",
                                    inline=True
                                )
                    except Exception as ex:
                        logger.error(f"Error retrieving data for player {user_id}: {ex}")
                        if i < 15:
                            embed.add_field(
                                name=f"{game_name} {tag_id}",
                                value="Error retrieving player data",
                                inline=True
                            )

                await interaction.response.send_message(embed=embed)

                # If there are more than 15 players, send additional messages
                if len(all_players) > 15:
                    remaining_embeds = []
                    current_embed = None

                    for i in range(15, len(all_players)):
                        # Create a new embed every 15 players
                        if i % 15 == 0:
                            current_embed = discord.Embed(
                                title=f"League of Legends Players (Continued {i // 15 + 1})",
                                color=discord.Color.blue()
                            )
                            remaining_embeds.append(current_embed)

                        user_id, game_name, tag_id = all_players[i]

                        # Get player stats
                        try:
                            db.cursor.execute(
                                "SELECT role, tier, rank, wins, losses, wr FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                                (user_id,)
                            )
                            game_data = db.cursor.fetchone()

                            if game_data:
                                role_data, tier, rank, wins, losses, win_rate = game_data

                                # Parse role preferences
                                role_str = "None"
                                if role_data:
                                    try:
                                        roles = json.loads(role_data)
                                        role_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
                                    except:
                                        role_str = str(role_data)

                                # Format tier and rank
                                tier_str = tier.capitalize() if tier else "Unranked"
                                rank_str = rank if rank else ""

                                # Calculate win rate if not provided
                                if win_rate is None and wins is not None and losses is not None:
                                    total_games = wins + losses
                                    if total_games > 0:
                                        win_rate = (wins / total_games) * 100
                                    else:
                                        win_rate = 0

                                # Format stats string
                                stats = f"**Rank:** {tier_str} {rank_str}\n"
                                if wins is not None and losses is not None:
                                    stats += f"**Record:** {wins}W {losses}L"
                                    if win_rate is not None:
                                        stats += f" ({win_rate:.1f}%)"

                                current_embed.add_field(
                                    name=f"{game_name} {tag_id}",
                                    value=f"{stats}\n**Roles:** {role_str}",
                                    inline=True
                                )
                            else:
                                current_embed.add_field(
                                    name=f"{game_name} {tag_id}",
                                    value="No game data available",
                                    inline=True
                                )
                        except Exception as ex:
                            logger.error(f"Error retrieving data for player {user_id}: {ex}")
                            current_embed.add_field(
                                name=f"{game_name} {tag_id}",
                                value="Error retrieving player data",
                                inline=True
                            )

                    for embed in remaining_embeds:
                        await interaction.followup.send(embed=embed)

            except Exception as ex:
                logger.error(f"Error listing players: {ex}")
                await interaction.response.send_message(f"Error listing players: {str(ex)}")
            finally:
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                    ephemeral=True)

    class VolunteerSelectionView(discord.ui.View):
        def __init__(self, players, needed_count, timeout=300):
            super().__init__(timeout=timeout)
            self.players = players
            self.needed_count = needed_count
            self.selected_players = []
            self.is_complete = False

            # Add player select menu
            self._add_player_select()
            self._add_action_buttons()

        def _add_player_select(self):
            # Create a select menu with player options
            options = []
            for player in self.players[:25]:  # Discord has a 25-option limit
                player_name = player.get('game_name', str(player.get('user_id')))
                tier = player.get('tier', 'unknown').capitalize()
                rank = player.get('rank', '')

                option = discord.SelectOption(
                    label=f"{player_name}",
                    description=f"{tier} {rank}",
                    value=str(player.get('user_id')),
                    default=player.get('user_id') in [p.get('user_id') for p in self.selected_players]
                )
                options.append(option)

            # Create select menu
            select = discord.ui.Select(
                placeholder="Select players to sit out...",
                min_values=0,
                max_values=min(len(options), self.needed_count),
                options=options
            )

            # Add callback
            select.callback = self.select_callback

            # Add select to view
            self.add_item(select)

        def _add_action_buttons(self):
            # Add a "Done" button
            done_button = discord.ui.Button(
                label=f"Confirm Selection ({len(self.selected_players)}/{self.needed_count})",
                style=discord.ButtonStyle.primary,
                disabled=len(self.selected_players) != self.needed_count,
                row=1
            )
            done_button.callback = self.done_callback
            self.add_item(done_button)

            # Add a "Random" button
            random_button = discord.ui.Button(
                label="Select Randomly",
                style=discord.ButtonStyle.danger,
                row=1
            )
            random_button.callback = self.random_callback
            self.add_item(random_button)

        async def select_callback(self, interaction):
            # Get selected player IDs from select menu
            selected_ids = [int(value) for value in interaction.data['values']]

            # Update selected players list
            self.selected_players = [p for p in self.players if p.get('user_id') in selected_ids]

            # Clear and rebuild the view
            self.clear_items()
            self._add_player_select()
            self._add_action_buttons()

            # Update the message
            await interaction.response.edit_message(
                content=f"Select {self.needed_count} volunteers to sit out (receiving participation points).\n"
                        f"Currently selected: {len(self.selected_players)}/{self.needed_count}",
                view=self
            )

        async def done_callback(self, interaction):
            if len(self.selected_players) == self.needed_count:
                self.is_complete = True
                self.stop()

                # Create a list of selected player names
                player_names = [f"{p.get('game_name')} ({p.get('tier', '').capitalize()} {p.get('rank', '')})"
                                for p in self.selected_players]

                await interaction.response.edit_message(
                    content=f"Selection complete! {self.needed_count} volunteers will sit out and receive participation points:\n" +
                            "\n".join([f"- {name}" for name in player_names]),
                    view=None
                )
            else:
                await interaction.response.send_message(
                    f"Please select exactly {self.needed_count} players before confirming.",
                    ephemeral=True
                )

        async def random_callback(self, interaction):
            # Select players randomly
            self.selected_players = random.sample(self.players, self.needed_count)
            self.is_complete = True
            self.stop()

            # Create a list of selected player names
            player_names = [f"{p.get('game_name')} ({p.get('tier', '').capitalize()} {p.get('rank', '')})"
                            for p in self.selected_players]

            await interaction.response.edit_message(
                content=f"Randomly selected {self.needed_count} players to sit out and receive participation points:\n" +
                        "\n".join([f"- {name}" for name in player_names]),
                view=None
            )

    @app_commands.command(name="simulate_volunteers", description="Simulate volunteers for sitting out")
    @app_commands.describe(count="Number of volunteers needed")
    async def simulate_volunteers(self, interaction: discord.Interaction, count: int = 4):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()

            try:
                # Get all players
                db.cursor.execute("""
                    SELECT p.user_id, p.game_name, p.tag_id, g.tier, g.rank 
                    FROM player p
                    JOIN game g ON p.user_id = g.user_id
                    GROUP BY p.user_id
                    HAVING MAX(g.game_date)
                """)

                all_players = []
                for record in db.cursor.fetchall():
                    user_id, game_name, tag_id, tier, rank = record
                    all_players.append({
                        'user_id': user_id,
                        'game_name': game_name,
                        'tier': tier.lower() if tier else 'default',
                        'rank': rank if rank else ''
                    })

                if len(all_players) < count:
                    await interaction.response.send_message(
                        f"Not enough players registered. Need at least {count} players, but only have {len(all_players)}."
                    )
                    return

                # Mark some players as "volunteering"
                volunteers = random.sample(all_players, count)

                # Create a volunteer table for demo
                volunteer_embed = discord.Embed(
                    title=f"Simulated Volunteers ({count} players)",
                    color=discord.Color.green(),
                    description="These players have volunteered to sit out and receive participation points."
                )

                for i, player in enumerate(volunteers):
                    name = player.get('game_name')
                    tier = player.get('tier', 'unknown').capitalize()
                    rank = player.get('rank', '')

                    volunteer_embed.add_field(
                        name=f"Player {i + 1}: {name}",
                        value=f"**Rank:** {tier} {rank}",
                        inline=True
                    )

                # Record volunteers in database with "volunteer" status
                session_id = f"volunteer_session_{int(asyncio.get_event_loop().time())}"
                for player in volunteers:
                    user_id = player.get('user_id')
                    if user_id:
                        query = "INSERT INTO Matches(user_id, teamUp, teamId) VALUES(?, ?, ?)"
                        db.cursor.execute(query, (user_id, "volunteer", session_id))

                db.connection.commit()
                db.close_db()

                await interaction.response.send_message(
                    content=f"Simulated {count} volunteers for sitting out.",
                    embed=volunteer_embed
                )

            except Exception as ex:
                logger.error(f"Error simulating volunteers: {ex}")
                await interaction.response.send_message(f"Error simulating volunteers: {str(ex)}")
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                    ephemeral=True)

    @app_commands.command(name="run_matchmaking", description="Run matchmaking with registered players")
    @app_commands.describe(
        players_per_game="Number of players per game (default: 10)",
        selection_method="How to select players who sit out: random, rank, or volunteer (default: random)"
    )
    async def run_matchmaking(
            self,
            interaction: discord.Interaction,
            players_per_game: int = 10,
            selection_method: str = "random"
    ):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)

            try:
                # Get all eligible players
                db = Tournament_DB()
                all_players = []

                try:
                    # Get all players with game data
                    db.cursor.execute("""
                        SELECT p.user_id, p.game_name, p.tag_id, g.tier, g.rank, g.role, g.wins, g.losses, g.wr
                        FROM player p
                        JOIN game g ON p.user_id = g.user_id
                        GROUP BY p.user_id
                        HAVING MAX(g.game_date)
                        ORDER BY 
                            CASE 
                                WHEN g.tier = 'challenger' THEN 1
                                WHEN g.tier = 'grandmaster' THEN 2
                                WHEN g.tier = 'master' THEN 3
                                WHEN g.tier = 'diamond' THEN 4
                                WHEN g.tier = 'emerald' THEN 5
                                WHEN g.tier = 'platinum' THEN 6
                                WHEN g.tier = 'gold' THEN 7
                                WHEN g.tier = 'silver' THEN 8
                                WHEN g.tier = 'bronze' THEN 9
                                WHEN g.tier = 'iron' THEN 10
                                ELSE 11
                            END, 
                            CASE 
                                WHEN g.rank = 'I' THEN 1
                                WHEN g.rank = 'II' THEN 2
                                WHEN g.rank = 'III' THEN 3
                                WHEN g.rank = 'IV' THEN 4
                                ELSE 5
                            END
                    """)

                    player_records = db.cursor.fetchall()

                    for record in player_records:
                        user_id, game_name, tag_id, tier, rank, role_json, wins, losses, wr = record

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
                            'tag_id': tag_id,
                            'tier': tier.lower() if tier else 'default',
                            'rank': rank if rank else 'V',
                            'role': roles,
                            'wins': wins if wins is not None else 0,
                            'losses': losses if losses is not None else 0,
                            'wr': float(wr) * 100 if wr is not None else 50.0
                        }

                        all_players.append(player)

                except Exception as ex:
                    logger.error(f"Error fetching players: {ex}")
                    await interaction.followup.send(f"Error fetching players: {str(ex)}")
                    db.close_db()
                    return

                # Calculate how many games we can run and if we need players to sit out
                total_players = len(all_players)

                if total_players < players_per_game:
                    await interaction.followup.send(
                        f"Not enough players for matchmaking. Need at least {players_per_game} players, but only have {total_players}."
                    )
                    db.close_db()
                    return

                game_count = total_players // players_per_game
                extra_players = total_players % players_per_game

                await interaction.followup.send(
                    f"Found {total_players} registered players.\n"
                    f"Can create {game_count} games with {players_per_game} players each.\n"
                    f"{extra_players} players will sit out and receive participation points."
                )

                # If we have extra players, determine who sits out
                players_to_exclude = []
                participation_players = []

                if extra_players > 0:
                    selection_method = selection_method.lower()

                    if selection_method == "rank":
                        # Use lowest ranked players
                        lowest_ranked_players = all_players[-extra_players:]
                        for player in lowest_ranked_players:
                            players_to_exclude.append(player['user_id'])
                            participation_players.append(player)

                        await interaction.followup.send(
                            f"**Using rank-based selection:** {extra_players} lowest-ranked players will sit out but receive participation points."
                        )

                    elif selection_method == "volunteer":
                        # Use interactive volunteer selection
                        await interaction.followup.send(
                            f"Please select {extra_players} volunteers to sit out (they will receive participation points)."
                        )

                        # Create volunteer selection view
                        view = self.VolunteerSelectionView(all_players, extra_players)
                        volunteer_msg = await interaction.followup.send(
                            content=f"Select {extra_players} volunteers to sit out (receiving participation points).\n"
                                    f"Currently selected: 0/{extra_players}",
                            view=view
                        )

                        # Wait for selection to complete
                        await view.wait()

                        if view.is_complete:
                            participation_players = view.selected_players
                            for player in participation_players:
                                players_to_exclude.append(player['user_id'])
                        else:
                            # Fallback to random if view timed out
                            random_players = random.sample(all_players, extra_players)
                            for player in random_players:
                                players_to_exclude.append(player['user_id'])
                                participation_players.append(player)

                            await interaction.followup.send(
                                f"Volunteer selection timed out. Falling back to random selection."
                            )

                    else:  # Default to random
                        # Randomly select players to sit out
                        random_players = random.sample(all_players, extra_players)
                        for player in random_players:
                            players_to_exclude.append(player['user_id'])
                            participation_players.append(player)

                        await interaction.followup.send(
                            f"**Using random selection:** {extra_players} randomly selected players will sit out but receive participation points."
                        )

                # Remove excluded players
                filtered_players = [p for p in all_players if p['user_id'] not in players_to_exclude]

                # Split players into pools based on skill
                filtered_players.sort(key=lambda p: (
                    {'challenger': 1, 'grandmaster': 2, 'master': 3, 'diamond': 4, 'emerald': 5,
                     'platinum': 6, 'gold': 7, 'silver': 8, 'bronze': 9, 'iron': 10}.get(p['tier'], 11),
                    {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}.get(p['rank'], 5),
                    -p.get('wr', 0)
                ))

                # Create pools for skill-based games
                pools = []
                for i in range(game_count):
                    start_idx = i * players_per_game
                    end_idx = start_idx + players_per_game
                    pool = filtered_players[start_idx:end_idx]
                    pools.append(pool)

                # Run matchmaking for each pool
                results = []
                matchmaker = GeneticMatchMaking()

                for pool_idx, pool in enumerate(pools):
                    # Create a match ID
                    match_id = f"match_{int(asyncio.get_event_loop().time())}_{pool_idx + 1}"

                    # Split pool into balanced teams
                    team1, team2 = [], []

                    # Process players with performance metrics
                    processed_players = await matchmaker.calculate_performance(pool)

                    # Run matchmaking
                    best_chromosome, best_fitness = matchmaker.genetic_algorithm(
                        processed_players,
                        population_size=100,
                        generations=100,
                        team_size=players_per_game // 2
                    )

                    if best_chromosome:
                        team1, team2 = matchmaker.decode_chromosome(
                            best_chromosome,
                            processed_players,
                            team_size=players_per_game // 2
                        )
                    else:
                        # Fallback: simple alternating assignment
                        for i, player in enumerate(pool):
                            if i % 2 == 0:
                                team1.append(player)
                            else:
                                team2.append(player)

                    # Record match in database
                    for player in team1:
                        user_id = player.get('user_id')
                        if user_id:
                            query = "INSERT INTO Matches(user_id, teamUp, teamId) VALUES(?, ?, ?)"
                            db.cursor.execute(query, (user_id, "team1", match_id))

                    for player in team2:
                        user_id = player.get('user_id')
                        if user_id:
                            query = "INSERT INTO Matches(user_id, teamUp, teamId) VALUES(?, ?, ?)"
                            db.cursor.execute(query, (user_id, "team2", match_id))

                    # Calculate team metrics
                    team1_perf = matchmaker.team_performance(team1)
                    team2_perf = matchmaker.team_performance(team2)
                    diff = abs(team1_perf - team2_perf)

                    # Create embeds for the teams
                    team1_embed = discord.Embed(
                        title=f"Game {pool_idx + 1} - Team 1 (Match ID: {match_id})",
                        color=discord.Color.blue(),
                        description=f"Game {pool_idx + 1} of {game_count}"
                    )

                    team2_embed = discord.Embed(
                        title=f"Game {pool_idx + 1} - Team 2 (Match ID: {match_id})",
                        color=discord.Color.red(),
                        description=f"Game {pool_idx + 1} of {game_count}"
                    )

                    # Add players to embeds
                    for i, player in enumerate(team1):
                        name = player.get('game_name', player.get('user_id', 'Unknown'))
                        tier = player.get('tier', 'Unknown').capitalize()
                        rank = player.get('rank', '')
                        roles = player.get('role', [])
                        role_str = ', '.join(roles) if roles else 'None'

                        # Try to get assigned role
                        assigned_role = roles[0] if roles else "TBD"

                        team1_embed.add_field(
                            name=f"Player {i + 1}: {name}",
                            value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}\n**Assigned:** {assigned_role}",
                            inline=True
                        )

                    for i, player in enumerate(team2):
                        name = player.get('game_name', player.get('user_id', 'Unknown'))
                        tier = player.get('tier', 'Unknown').capitalize()
                        rank = player.get('rank', '')
                        roles = player.get('role', [])
                        role_str = ', '.join(roles) if roles else 'None'

                        # Try to get assigned role
                        assigned_role = roles[0] if roles else "TBD"

                        team2_embed.add_field(
                            name=f"Player {i + 1}: {name}",
                            value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}\n**Assigned:** {assigned_role}",
                            inline=True
                        )

                    # Add metrics to embeds
                    team1_embed.set_footer(text=f"Team 1 Performance: {team1_perf:.2f}")
                    team2_embed.set_footer(text=f"Team 2 Performance: {team2_perf:.2f}")

                    # Instructions for recording match outcome
                    instructions = (
                        f"**Matchmaking - Game {pool_idx + 1} of {game_count}**\n"
                        f"Match ID: `{match_id}`\n"
                        f"Team Performance Difference: {diff:.2f}\n\n"
                        f"To record match results, use: `/record_match_result {match_id} <winning_team>`\n"
                        f"where <winning_team> is either 1 or 2."
                    )

                    results.append({
                        "match_id": match_id,
                        "pool_idx": pool_idx,
                        "embeds": [team1_embed, team2_embed],
                        "instructions": instructions
                    })

                # Record participation points for excluded players
                if participation_players:
                    participation_id = f"participation_{int(asyncio.get_event_loop().time())}"
                    for player in participation_players:
                        user_id = player.get('user_id')
                        if user_id:
                            query = "INSERT INTO Matches(user_id, teamUp, teamId) VALUES(?, ?, ?)"
                            db.cursor.execute(query, (user_id, "participation", participation_id))

                # Commit all changes to database
                db.connection.commit()
                db.close_db()

                # Send results for each game
                for result in results:
                    await interaction.followup.send(content=result["instructions"], embeds=result["embeds"])

                # If there were participation players, show them too
                if participation_players:
                    participation_embed = discord.Embed(
                        title="Players Receiving Participation Points",
                        color=discord.Color.green(),
                        description=f"{len(participation_players)} players are sitting out but will receive participation points."
                    )

                    for i, player in enumerate(participation_players):
                        name = player.get('game_name', player.get('user_id', 'Unknown'))
                        tier = player.get('tier', 'Unknown').capitalize()
                        rank = player.get('rank', '')

                        participation_embed.add_field(
                            name=f"Player {i + 1}: {name}",
                            value=f"**Rank:** {tier} {rank}",
                            inline=True
                        )

                    await interaction.followup.send(embed=participation_embed)

            except Exception as ex:
                logger.error(f"Error running matchmaking: {ex}")
                await interaction.followup.send(f"Error running matchmaking: {str(ex)}")
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                    ephemeral=True)

    # Create a class for match result selection
    class MatchResultView(discord.ui.View):
        def __init__(self, match_results, timeout=300):
            super().__init__(timeout=timeout)
            self.match_results = match_results
            self.processed_results = {}

            # Add select menu for match selection
            self._add_match_select()
            self._add_team_buttons()

        def _add_match_select(self):
            # Create options for each match
            options = []
            for match_data in self.match_results:
                match_id = match_data['match_id']
                pool_idx = match_data['pool_idx']
                is_processed = match_id in self.processed_results

                option = discord.SelectOption(
                    label=f"Game {pool_idx + 1}",
                    description=f"Match ID: {match_id}",
                    value=match_id,
                    default=False,
                    emoji="✅" if is_processed else "⏱️"
                )
                options.append(option)

            # Create select menu
            select = discord.ui.Select(
                placeholder="Select match to record result...",
                options=options
            )

            # Add callback
            select.callback = self.match_select_callback

            # Add to view
            self.add_item(select)

        def _add_team_buttons(self):
            # Team 1 button
            team1_button = discord.ui.Button(
                label="Team 1 Wins",
                style=discord.ButtonStyle.success,
                row=1
            )
            team1_button.callback = self.create_team_callback(1)
            self.add_item(team1_button)

            # Team 2 button
            team2_button = discord.ui.Button(
                label="Team 2 Wins",
                style=discord.ButtonStyle.danger,
                row=1
            )
            team2_button.callback = self.create_team_callback(2)
            self.add_item(team2_button)

            # Add "Done" button
            done_button = discord.ui.Button(
                label="Finish Recording",
                style=discord.ButtonStyle.primary,
                row=2
            )
            done_button.callback = self.done_callback
            self.add_item(done_button)

        def create_team_callback(self, team_number):
            async def callback(interaction):
                # Get the currently selected match
                selected_match_id = None
                for item in self.children:
                    if isinstance(item, discord.ui.Select):
                        selected_match_id = item.values[0] if item.values else None

                if not selected_match_id:
                    await interaction.response.send_message(
                        "Please select a match first before recording the result.",
                        ephemeral=True
                    )
                    return

                # Record the result
                self.processed_results[selected_match_id] = team_number

                # Rebuild the view
                self.clear_items()
                self._add_match_select()
                self._add_team_buttons()

                await interaction.response.edit_message(
                    content=f"Recording match results...\n"
                            f"Match {selected_match_id}: Team {team_number} wins!\n"
                            f"Recorded results for {len(self.processed_results)}/{len(self.match_results)} matches.",
                    view=self
                )

            return callback

        async def match_select_callback(self, interaction):
            # Just acknowledge - team buttons will be used for actual action
            await interaction.response.defer()

        async def done_callback(self, interaction):
            # If we have all results, or admin wants to finish early
            missing_matches = len(self.match_results) - len(self.processed_results)

            if missing_matches > 0:
                # Ask for confirmation if not all matches recorded
                confirm_content = f"You have {missing_matches} unrecorded match results. Are you sure you want to finish?"
                confirm_view = self.ConfirmFinishView(self)

                await interaction.response.send_message(
                    content=confirm_content,
                    view=confirm_view,
                    ephemeral=True
                )
            else:
                # All matches recorded, finish up
                self.stop()
                await interaction.response.edit_message(
                    content=f"All {len(self.match_results)} match results recorded successfully!",
                    view=None
                )

        # Nested confirmation view class
        class ConfirmFinishView(discord.ui.View):
            def __init__(self, parent_view):
                super().__init__(timeout=60)
                self.parent_view = parent_view

            @discord.ui.button(label="Yes, finish recording", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction, button):
                self.parent_view.stop()
                await interaction.response.edit_message(
                    content="Recording finished.",
                    view=None
                )
                await interaction.followup.edit_message(
                    message_id=self.parent_view.message.id,
                    content=f"Match recording completed. {len(self.parent_view.processed_results)}/{len(self.parent_view.match_results)} matches recorded.",
                    view=None
                )

            @discord.ui.button(label="No, continue recording", style=discord.ButtonStyle.success)
            async def cancel(self, interaction, button):
                await interaction.response.edit_message(
                    content="Continuing with result recording...",
                    view=None
                )

    @app_commands.command(name="record_match_results", description="Record the outcomes of multiple matches")
    async def record_match_results(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            # Get recent matches that don't have results yet
            db = Tournament_DB()
            try:
                # Look for matches without win/loss recorded
                db.cursor.execute("""
                    SELECT DISTINCT teamId, MAX(date_played) 
                    FROM Matches 
                    WHERE win IS NULL AND loss IS NULL
                    GROUP BY teamId
                    ORDER BY MAX(date_played) DESC
                    LIMIT 10
                """)

                recent_matches = db.cursor.fetchall()

                if not recent_matches:
                    await interaction.response.send_message("No pending matches found to record results for.")
                    db.close_db()
                    return

                # Prepare match data for the view
                match_results = []

                for i, (match_id, _) in enumerate(recent_matches):
                    match_results.append({
                        "match_id": match_id,
                        "pool_idx": i
                    })

                # Create view for match results
                view = self.MatchResultView(match_results)

                # Send initial message
                response = await interaction.response.send_message(
                    content=f"Found {len(match_results)} matches needing results.\n"
                            f"Select a match and then click the team that won.",
                    view=view
                )

                # Store message reference for later updates
                view.message = await interaction.original_response()

                # Wait for the view to complete
                await view.wait()

                # Process the results
                results_processed = 0

                for match_id, winning_team in view.processed_results.items():
                    # Update winners
                    winning_team_name = f"team{winning_team}"
                    losing_team_name = f"team{3 - winning_team}"  # If winning_team is 1, losing is 2 and vice versa

                    # Update winners
                    db.cursor.execute(
                        "UPDATE Matches SET win = 'yes', loss = 'no' WHERE teamId = ? AND teamUp = ?",
                        (match_id, winning_team_name)
                    )
                    winners_updated = db.cursor.rowcount
                    logger.info(f"Updated {winners_updated} winners for match {match_id}, team {winning_team_name}")

                    # Update losers
                    db.cursor.execute(
                        "UPDATE Matches SET win = 'no', loss = 'yes' WHERE teamId = ? AND teamUp = ?",
                        (match_id, losing_team_name)
                    )
                    losers_updated = db.cursor.rowcount
                    logger.info(f"Updated {losers_updated} losers for match {match_id}, team {losing_team_name}")

                    # Get player stats to update
                    db.cursor.execute(
                        "SELECT user_id, teamUp FROM Matches WHERE teamId = ?",
                        (match_id,)
                    )
                    players = db.cursor.fetchall()

                    # Update player stats in the Game table
                    for player_id, team in players:
                        # Get current player stats
                        db.cursor.execute(
                            "SELECT wins, losses FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                            (player_id,)
                        )
                        result = db.cursor.fetchone()

                        if result:
                            current_wins, current_losses = result

                            # Set default values if None
                            current_wins = current_wins if current_wins is not None else 0
                            current_losses = current_losses if current_losses is not None else 0

                            # Update based on match result
                            if team == winning_team_name:
                                new_wins = current_wins + 1
                                update_query = """
                                    UPDATE game SET wins = ?
                                    WHERE user_id = ? AND game_date = (
                                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                                    )
                                """
                                db.cursor.execute(update_query, (new_wins, player_id, player_id))
                            elif team == losing_team_name:  # Exclude participation players
                                new_losses = current_losses + 1
                                update_query = """
                                    UPDATE game SET losses = ?
                                    WHERE user_id = ? AND game_date = (
                                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                                    )
                                """
                                db.cursor.execute(update_query, (new_losses, player_id, player_id))

                    # Make sure to commit changes after each match is processed
                    db.connection.commit()
                    logger.info(f"Committed changes for match {match_id}")

                    results_processed += 1

                # Final commit for any remaining changes
                db.connection.commit()
                logger.info(f"Final commit complete, processed {results_processed} matches")

                # Send final confirmation
                if results_processed > 0:
                    await interaction.followup.send(
                        f"Successfully recorded results for {results_processed} matches and updated player stats."
                    )

            except Exception as ex:
                logger.error(f"Error recording match results: {ex}")
                await interaction.followup.send(f"Error recording match results: {str(ex)}")
            finally:
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                    ephemeral=True)

    @app_commands.command(name="record_match_result", description="Record the outcome of a single match")
    @app_commands.describe(
        match_id="The ID of the match (from run_matchmaking command)",
        winning_team="The number of the winning team (1 or 2)"
    )
    async def record_match_result(self, interaction: discord.Interaction, match_id: str, winning_team: int):
        if interaction.user.guild_permissions.administrator:
            if winning_team not in [1, 2]:
                await interaction.response.send_message("Winning team must be either 1 or 2", ephemeral=True)
                return

            db = Tournament_DB()
            try:
                # Verify the match exists
                db.cursor.execute("SELECT COUNT(*) FROM Matches WHERE teamId = ?", (match_id,))
                count = db.cursor.fetchone()[0]

                if count == 0:
                    await interaction.response.send_message(f"Match ID {match_id} not found", ephemeral=True)
                    return

                # Update the match results
                winning_team_name = f"team{winning_team}"
                losing_team_name = f"team{3 - winning_team}"  # If winning_team is 1, losing is 2 and vice versa

                # Update winners
                db.cursor.execute(
                    "UPDATE Matches SET win = 'yes', loss = 'no' WHERE teamId = ? AND teamUp = ?",
                    (match_id, winning_team_name)
                )
                winners_updated = db.cursor.rowcount
                logger.info(f"Updated {winners_updated} winners for match {match_id}, team {winning_team_name}")

                # Update losers
                db.cursor.execute(
                    "UPDATE Matches SET win = 'no', loss = 'yes' WHERE teamId = ? AND teamUp = ?",
                    (match_id, losing_team_name)
                )
                losers_updated = db.cursor.rowcount
                logger.info(f"Updated {losers_updated} losers for match {match_id}, team {losing_team_name}")

                # Get player stats to update
                db.cursor.execute(
                    "SELECT user_id, teamUp FROM Matches WHERE teamId = ?",
                    (match_id,)
                )
                players = db.cursor.fetchall()

                # Update player stats in the Game table
                players_updated = 0
                for player_id, team in players:
                    # Get current player stats
                    db.cursor.execute(
                        "SELECT wins, losses FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                        (player_id,)
                    )
                    result = db.cursor.fetchone()

                    if result:
                        current_wins, current_losses = result

                        # Set default values if None
                        current_wins = current_wins if current_wins is not None else 0
                        current_losses = current_losses if current_losses is not None else 0

                        # Update based on match result
                        if team == winning_team_name:
                            new_wins = current_wins + 1
                            update_query = """
                                UPDATE game SET wins = ?
                                WHERE user_id = ? AND game_date = (
                                    SELECT MAX(game_date) FROM game WHERE user_id = ?
                                )
                            """
                            db.cursor.execute(update_query, (new_wins, player_id, player_id))
                        else:
                            new_losses = current_losses + 1
                            update_query = """
                                UPDATE game SET losses = ?
                                WHERE user_id = ? AND game_date = (
                                    SELECT MAX(game_date) FROM game WHERE user_id = ?
                                )
                            """
                            db.cursor.execute(update_query, (new_losses, player_id, player_id))

                        players_updated += 1

                # Commit all changes - do this explicitly
                logger.info(f"About to commit changes for match {match_id}")
                db.connection.commit()
                logger.info(f"Successfully committed changes for match {match_id}")

                # Send confirmation
                await interaction.response.send_message(
                    f"Match {match_id} result recorded: Team {winning_team} wins!\n"
                    f"Updated stats for {players_updated} players."
                )

            except Exception as ex:
                logger.error(f"Error recording match result: {ex}")
                await interaction.response.send_message(f"Error recording match result: {str(ex)}")
            finally:
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                    ephemeral=True)

    @app_commands.command(name="player_match_history", description="View a player's match history")
    @app_commands.describe(player_name="The summoner name of the player to look up")
    async def player_match_history(self, interaction: discord.Interaction, player_name: str):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()
            try:
                # Find player ID from name
                db.cursor.execute("SELECT user_id FROM player WHERE game_name LIKE ?", (f"%{player_name}%",))
                result = db.cursor.fetchone()

                if not result:
                    await interaction.response.send_message(f"Player '{player_name}' not found", ephemeral=True)
                    return

                player_id = result[0]

                # Get player details
                db.cursor.execute("SELECT game_name, tag_id FROM player WHERE user_id = ?", (player_id,))
                player_data = db.cursor.fetchone()
                game_name, tag_id = player_data

                # Get player stats
                db.cursor.execute(
                    "SELECT tier, rank, role, wins, losses, wr FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (player_id,)
                )
                game_data = db.cursor.fetchone()

                if not game_data:
                    await interaction.response.send_message(f"No game data found for player '{player_name}'",
                                                            ephemeral=True)
                    return

                tier, rank, role_json, wins, losses, win_rate = game_data

                # Parse role preferences
                role_str = "None"
                if role_json:
                    try:
                        roles = json.loads(role_json)
                        role_str = ', '.join(roles) if isinstance(roles, list) else str(roles)
                    except:
                        role_str = str(role_json)

                # Get match history
                db.cursor.execute(
                    """
                    SELECT m.teamId, m.teamUp, m.win, m.loss, m.date_played 
                    FROM Matches m
                    WHERE m.user_id = ?
                    ORDER BY m.date_played DESC
                    LIMIT 10
                    """,
                    (player_id,)
                )
                matches = db.cursor.fetchall()

                # Create player profile embed
                embed = discord.Embed(
                    title=f"Player Profile: {game_name} {tag_id}",
                    color=discord.Color.gold()
                )

                # Add player stats
                embed.add_field(
                    name="Rank",
                    value=f"{tier.capitalize() if tier else 'Unranked'} {rank if rank else ''}",
                    inline=True
                )

                embed.add_field(
                    name="Win/Loss",
                    value=f"{wins}W {losses}L" if wins is not None and losses is not None else "No record",
                    inline=True
                )

                if wins is not None and losses is not None:
                    total_games = wins + losses
                    if total_games > 0:
                        calculated_wr = (wins / total_games) * 100
                        embed.add_field(
                            name="Win Rate",
                            value=f"{calculated_wr:.1f}%",
                            inline=True
                        )

                embed.add_field(
                    name="Preferred Roles",
                    value=role_str,
                    inline=False
                )

                # Add match history
                if matches:
                    match_history = ""
                    for match in matches:
                        match_id, team, win, loss, date = match
                        result = "Win" if win == "yes" else "Loss" if loss == "yes" else "Unknown"
                        match_date = date if date else "Unknown date"
                        match_history += f"**{match_id}**: {result} (Team {team[-1]}) - {match_date}\n"

                    embed.add_field(
                        name="Recent Matches",
                        value=match_history if match_history else "No match history",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Recent Matches",
                        value="No match history found",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)

            except Exception as ex:
                logger.error(f"Error retrieving player history: {ex}")
                await interaction.response.send_message(f"Error retrieving player history: {str(ex)}")
            finally:
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                    ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin_commands(bot))
