import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.tasks import Tasks_Collection

@pytest.mark.asyncio
async def test_promote_player_tier():
    dummy_bot = MagicMock()
    dummy_bot.wait_until_ready = AsyncMock()
    obj = Tasks_Collection(bot=dummy_bot)
    obj.min_game_played = 10
    obj.win_rate = 62
    obj.max_game_lost = 15
    obj.tier_list = ['bronze', 'silver', 'gold', 'platinum']

    # Simulated player data:
    # [player_id, tier, games_played, win_rate]
    mock_data = [
        [1, 'silver', 12, 65],   # should be promoted to gold
        [2, 'gold', 20, 45],     # should be demoted to silver
        [3, 'bronze', 5, 80],    # not enough games, no promotion
    ]

    with patch('common.tasks.Player_game_info.fetch_for_tier_promotion', return_value=mock_data), \
         patch('common.tasks.Player_game_info.update_tier') as mock_update, \
         patch('common.tasks.Tournament_DB') as mock_db:
        
        mock_db.return_value.close_db = MagicMock()
        
        await obj.promote_player_tier()

        # Check promotion
        mock_update.assert_any_call(mock_db.return_value, 1, 'gold')
        # Check demotion
        mock_update.assert_any_call(mock_db.return_value, 2, 'silver')
        # Should not update for player 3
        assert mock_update.call_count == 2
