import unittest
import sys
import os
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.team_swap_controller import TeamSwapController
from model.dbc_model import Tournament_DB, Matches

class TestTeamSwap(unittest.TestCase):
    
    def setUp(self):
        # Mock the bot
        self.bot = MagicMock()
        
        # Create controller
        self.controller = TeamSwapController(self.bot)
        
        # Set up test data
        self.match_id = "test_match_1"
        self.player1_id = 123456789
        self.player2_id = 987654321
        
    @patch.object(Tournament_DB, 'db_connect')
    @patch.object(Tournament_DB, 'close_db')
    @patch.object(Tournament_DB, 'cursor')
    @patch.object(Tournament_DB, 'connection')
    def test_swap_players_success(self, mock_connection, mock_cursor, mock_close_db, mock_db_connect):
        # Setup mocks
        mock_cursor.fetchone.side_effect = [
            ("team1",),   # First player's team
            ("team2",),   # Second player's team
        ]
        
        # Run the function asynchronously
        result = asyncio.run(self.controller.swap_players(self.match_id, self.player1_id, self.player2_id))
        
        # Check results
        self.assertTrue(result)
        
        # Verify correct database operations were performed
        mock_cursor.execute.assert_any_call(
            "SELECT teamUp FROM Matches WHERE teamId = ? AND user_id = ?",
            (self.match_id, self.player1_id)
        )
        
        mock_cursor.execute.assert_any_call(
            "SELECT teamUp FROM Matches WHERE teamId = ? AND user_id = ?",
            (self.match_id, self.player2_id)
        )
        
        mock_cursor.execute.assert_any_call(
            "UPDATE Matches SET teamUp = ? WHERE teamId = ? AND user_id = ?",
            ("team2", self.match_id, self.player1_id)
        )
        
        mock_cursor.execute.assert_any_call(
            "UPDATE Matches SET teamUp = ? WHERE teamId = ? AND user_id = ?",
            ("team1", self.match_id, self.player2_id)
        )
        
        mock_connection.commit.assert_called_once()
        mock_close_db.assert_called_once()
    
    @patch.object(Tournament_DB, 'db_connect')
    @patch.object(Tournament_DB, 'close_db')
    @patch.object(Tournament_DB, 'cursor')
    def test_swap_players_not_found(self, mock_cursor, mock_close_db, mock_db_connect):
        # Setup mocks - player not found
        mock_cursor.fetchone.side_effect = [None, None]
        
        # Run the function asynchronously
        result = asyncio.run(self.controller.swap_players(self.match_id, self.player1_id, self.player2_id))
        
        # Check results
        self.assertFalse(result)
        mock_close_db.assert_called_once()

if __name__ == '__main__':
    unittest.main()