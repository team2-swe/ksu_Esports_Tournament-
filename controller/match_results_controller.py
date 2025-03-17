import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Player, Game

logger = settings.logging.getLogger("discord")

class MatchResultsController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
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


async def setup(bot):
    await bot.add_cog(MatchResultsController(bot))