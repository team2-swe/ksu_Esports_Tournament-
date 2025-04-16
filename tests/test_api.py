import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from controller.api import ApiCommon, Api_Collection

mock_account_info = {"puuid": "test-puuid"}
mock_result_format = {"id": "test-summoner-id"}
mock_final_response = [{"tier": "Platinum", "rank": "II"}]


@pytest.mark.asyncio
@patch("controller.api.requests.get")
async def test_get_player_details_success(mock_get):
    # Simulate all 3 API requests being successful
    mock_get.side_effect = [
        MagicMock(status_code=200, json=lambda: mock_account_info),
        MagicMock(status_code=200, json=lambda: mock_result_format),
        MagicMock(status_code=200, json=lambda: mock_final_response),
    ]

    result = await ApiCommon.get_player_details("testName", "testId")
    assert result == mock_final_response


@pytest.mark.asyncio
@patch("controller.api.requests.get")
async def test_get_player_details_fail(mock_get):
    # First request fails
    mock_get.return_value = MagicMock(status_code=404)

    result = await ApiCommon.get_player_details("testName", "testId")
    assert result is None


@pytest.mark.asyncio
@patch("controller.api.Tournament_DB")
@patch("controller.api.Player_game_info.update_player_API_info")
@patch("controller.api.Player.remove_player")
@patch("controller.api.ApiCommon.get_player_details", new_callable=AsyncMock)
async def test_push_player_info_with_data(mock_get_details, mock_remove, mock_update, mock_db):
    mock_get_details.return_value = [{"tier": "Gold", "rank": "IV"}]

    await ApiCommon.push_player_info("player123", "name", "id")

    mock_update.assert_called_once_with(mock_db.return_value, "player123", "Gold", "IV", 0, 0)
    mock_remove.assert_not_called()
    mock_db.return_value.close_db.assert_called_once()


@pytest.mark.asyncio
@patch("controller.api.Tournament_DB")
@patch("controller.api.Player_game_info.update_player_API_info")
@patch("controller.api.Player.remove_player")
@patch("controller.api.ApiCommon.get_player_details", new_callable=AsyncMock)
async def test_push_player_info_no_data(mock_get_details, mock_remove, mock_update, mock_db):
    mock_get_details.return_value = None

    await ApiCommon.push_player_info("player456", "name", "id")

    mock_update.assert_not_called()
    mock_remove.assert_called_once_with(mock_db.return_value, "player456")
    mock_db.return_value.close_db.assert_called_once()


@pytest.mark.asyncio
@patch("controller.api.Tournament_DB")
@patch("controller.api.Player.get_players")
@patch("controller.api.ApiCommon.push_player_info", new_callable=AsyncMock)
async def test_fetch_players_details(mock_push_info, mock_get_players, mock_db):
    mock_get_players.return_value = [
        ("player1", "testname1", "id1"),
        ("player2", "testname2", "id2"),
    ]

    bot = MagicMock()
    api_collector = Api_Collection(bot)

    # Call the actual loop method directly
    await api_collector.fetch_players_details()

    assert mock_push_info.call_count == 2
    mock_db.return_value.close_db.assert_called_once()
