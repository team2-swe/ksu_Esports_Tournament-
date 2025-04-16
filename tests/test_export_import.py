import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import discord
from controller.export_import import Import_Export, Player_game_info, Player

# Let's assume your class is named Import_Export
# from your_module import Import_Export

@pytest.fixture
def handler():
    handler = MagicMock()
    handler.googleSheetId = "fake_sheet_id"
    return handler

def test_isSheetExists_true(handler):
    handler.spreadsheets_service.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "TestSheet"}}]
    }
    handler.isSheetExists = Import_Export.isSheetExists.__get__(handler)
    assert handler.isSheetExists("TestSheet") is True

def test_isSheetExists_false(handler):
    handler.spreadsheets_service.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "OtherSheet"}}]
    }
    handler.isSheetExists = Import_Export.isSheetExists.__get__(handler)
    assert handler.isSheetExists("TestSheet") is False

@pytest.mark.asyncio
async def test_sheets_create_add_sheet(handler):
    handler.isSheetExists = MagicMock(return_value=False)
    handler.spreadsheets_service.batchUpdate.return_value.execute.return_value = {
        "replies": [{"addSheet": {"properties": {"sheetId": 123456}}}]
    }

    handler.sheets_create = Import_Export.sheets_create.__get__(handler)
    result = await handler.sheets_create("NewSheet", False)
    assert result == 123456

@pytest.mark.asyncio
async def test_sheets_create_clear(handler):
    handler.isSheetExists = MagicMock(return_value=True)
    handler.spreadsheets_service.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "NewSheet", "sheetId": 999}}]
    }

    handler.sheets_create = Import_Export.sheets_create.__get__(handler)
    result = await handler.sheets_create("NewSheet", True)
    assert result == 999

@pytest.mark.asyncio
async def test_exportToGoogleSheet_admin():
    mock_bot = MagicMock()
    mock_interaction = MagicMock(spec=discord.Interaction)
    mock_interaction.user.guild_permissions.administrator = True
    mock_interaction.response.defer = AsyncMock()
    mock_interaction.followup.send = AsyncMock()

    # 2. Instantiate Cog with mock bot
    handler = Import_Export(mock_bot)
    handler.googleSheetId = "test_sheet_id"

    #Mock internal methods and dependencies
    handler.sheets_create = AsyncMock()
    handler.spreadsheets_service = MagicMock()
    handler.spreadsheets_service.values().update.return_value.execute = MagicMock()

    Player_game_info.exportToGoogleSheet = MagicMock(return_value=(["id", "name"], [[1, "test"]]))
    db_mock = MagicMock()
    Tournament_DB = MagicMock(return_value=db_mock)

    # handler.exportToGoogleSheet = Import_Export.exportToGoogleSheet.__get__(handler)
    

    #Patch DB and player info
    with patch("controller.export_import.Tournament_DB", Tournament_DB), \
         patch("controller.export_import.Player_game_info", Player_game_info):
        await Import_Export.exportToGoogleSheet.callback(handler, mock_interaction)
        # await handler.exportToGoogleSheet(mock_interaction)

    mock_interaction.followup.send.assert_called()

@pytest.mark.asyncio
async def test_importFromGoogleSheet_admin():
    mock_bot = MagicMock()
    handler = Import_Export(mock_bot)
    handler.googleSheetId = "fake_sheet_id"
    # Mock required attributes on the handler
    handler.spreadsheets_service = MagicMock()
    handler.spreadsheets_service.values().get.return_value.execute.return_value = {
        "values": [["player_id", "score"], ["p1", "100"]]
    }

    mock_interaction = MagicMock(spec=discord.Interaction)
    mock_interaction.user.guild_permissions.administrator = True
    mock_interaction.response.defer = AsyncMock()
    mock_interaction.followup.send = AsyncMock()

    sheet_data_mock = {
        "values": [["player_id", "score"], ["p1", "100"]]
    }
    handler.spreadsheets_service.values().get.return_value.execute.return_value = sheet_data_mock

    db_mock = MagicMock()
    Tournament_DB = MagicMock(return_value=db_mock)

    Player_game_info.metadata = MagicMock(return_value=[(0, "player_id"), (1, "score")])
    Player.metadata = MagicMock(return_value=[(0, "player_id")])
    Player.generalplayerQuery = MagicMock()
    Player_game_info.isExistPlayerId = MagicMock(return_value=False)
    Player_game_info.importToDb = MagicMock()

    # handler.importFromGoogleSheet = Import_Export.importFromGoogleSheet.__get__(handler)

    with patch("controller.export_import.Tournament_DB", Tournament_DB), \
         patch("controller.export_import.Player_game_info", Player_game_info), \
         patch("controller.export_import.Player", Player):
        await Import_Export.importFromGoogleSheet.callback(handler, mock_interaction, "Sheet1")

    mock_interaction.followup.send.assert_called_with("✅ Data Imported and Updated Successfully!")

