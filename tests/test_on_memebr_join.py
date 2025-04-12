import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller.events import EventsController
from model import dbc_model
from view.signUp_view import SignUpView
from common import common_scripts

@pytest.fixture
def mock_bot():
    return MagicMock(spec=commands.Bot)

@pytest.fixture
def mock_member():
    member = MagicMock(spec=discord.Member)
    member.id = 123
    member.guild.name = "Test Server"
    member.send = AsyncMock()
    return member

@pytest.fixture
def events_controller(mock_bot):
    return EventsController(mock_bot)

@pytest.fixture
def mock_db():
    mock_db = MagicMock(spec=dbc_model.Tournament_DB)
    mock_db.close_db = MagicMock()
    return mock_db

@pytest.fixture
def mock_sign_up_view():
    view = MagicMock(spec=SignUpView)
    view.children = True
    view.wait = AsyncMock()
    return view

@pytest.fixture
def mock_common_scripts():
    with patch('common.common_scripts.get_ksu_logo', return_value='/common\images/KSU _Esports_Tournament.png'):
        with patch('common.common_scripts.ksu_img_resize', return_value=('/common\images/KSU _Esports_Tournament.png', '.png')):
            yield

@pytest.mark.asyncio
async def test_on_member_join_new_member(events_controller, mock_member, mock_db, mock_sign_up_view, mock_common_scripts):
    # Mocking discord.Embed and discord.File
    with patch('discord.Embed') as MockEmbed, patch('discord.File') as MockFile:
        # Create mock instances of Embed and File
        mock_embed_instance = MagicMock()
        mock_file_instance = MagicMock()
        
        # Set the mock return values
        MockEmbed.return_value = mock_embed_instance
        MockFile.return_value = mock_file_instance

        # Mocking the database method to return False for isMemberExist
        with patch.object(dbc_model.Player, 'isMemberExist', return_value=False):
            await events_controller.on_member_join(mock_member)

            # Verify that the discord.Embed was created and passed to the send method
            MockEmbed.assert_called_once_with(
                color=discord.Colour.dark_teal(),
                description="seooewow ...... mlnsknfs ...",
                title=f"Welcome to {mock_member.guild.name} server"
            )

            # Verify that the discord.File was created and passed to the send method
            MockFile.assert_called_once_with('mock_resized_logo', filename='resized_logo.png')

            # Verify that the member's send method was called with the mock embed and file
            mock_member.send.assert_called_once_with(embed=mock_embed_instance, file=mock_file_instance)

            # Assert that the embed has a thumbnail set
            mock_embed_instance.set_thumbnail.assert_called_once_with(url="attachment://resized_logo.png")


'''
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller.events import EventsController

# Mocking the necessary components
@pytest.fixture
def mock_db():
    mock_db_instance = MagicMock()
    mock_db_instance.close.return_value = None
    return mock_db_instance

@pytest.fixture
def mock_member():
    mock_member = MagicMock(spec=discord.Member)
    mock_member.id = 12345
    mock_member.guild.name = "Test Server"
    return mock_member

@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=commands.Bot)
    return bot

@pytest.fixture
def mock_sign_up_view(spec=discord.ui.View):
    mock_view = MagicMock(spec=discord.ui.View)
    mock_view.message = MagicMock()
    mock_view.message.send = AsyncMock()
    mock_view.children = [MagicMock(), MagicMock()]
    mock_view.wait = AsyncMock()
    return mock_view

@pytest.fixture
def mock_events_controller(mock_bot):
    return EventsController(mock_bot)

# Test case for the on_member_join event
@patch('discord.File')
@patch('controller.events.common_scripts.ksu_img_resize')
@patch('controller.events.common_scripts.get_ksu_logo')
@patch('controller.events.dbc_model.Player.isMemberExist')
@patch('controller.events.dbc_model.Tournament_DB')

@pytest.mark.asyncio
async def test_on_member_join(
    mock_tournament_db,
    mock_isMemberExist,
    mock_get_ksu_logo,
    mock_ksu_img_resize,
    mock_file,
    mock_db,
    mock_member,
    mock_bot,
    mock_sign_up_view,
    mock_events_controller
):
    # Mock database return value
    mock_isMemberExist.return_value = False

    mock_tournament_db.return_value = mock_db
    # Mock logo functions
    mock_get_ksu_logo.return_value = '/common\images/KSU _Esports_Tournament.png'
    mock_ksu_img_resize.return_value = ('/common\images/KSU _Esports_Tournament.png', '.png')

    mock_sign_up_view.message.send.return_value = mock_sign_up_view.message
    # Mock the children of the view
    mock_sign_up_view.children = [MagicMock(), MagicMock()]
    # Mock the bot's send method
    mock_member.send = AsyncMock()
    # Simulate member joining
    await mock_events_controller.on_member_join(mock_member)

    # Test if the database check was performed
    mock_isMemberExist.assert_called_with(mock_db, mock_member.id)

    # Test if logo fetching and resizing were called
    mock_get_ksu_logo.assert_called_once()
    mock_ksu_img_resize.assert_called_once_with('path/to/ksu_logo.png')

    # Test if the embed was sent to the user
    mock_member.send.assert_called()

    # Test if the signup view is sent
    mock_sign_up_view.wait.assert_called()

    # Test if an embed was sent with the correct parameters
    embed = mock_member.send.call_args[0][0]  # Getting the first argument passed to send (which should be the embed)
    assert embed.title == f"Welcome to {mock_member.guild.name} server"
    assert embed.color == discord.Colour.dark_teal()

    # Check if the file attachment (logo) was sent correctly
    file = mock_member.send.call_args[0][1]  # Getting the second argument (the file)
    assert file.filename == "resized_logo.png"



import pytest
from unittest.mock import MagicMock, AsyncMock
from controller.events import EventsController
import discord

# Fixtures for mocking

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    return bot

@pytest.fixture
def mock_member():
    member = MagicMock(spec=discord.Member)
    member.id = 123456789
    member.guild.name = "Test Guild"
    return member

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

@pytest.fixture
def mock_sign_up_view():
    from controller.events import SignUpView
    view = MagicMock(spec=SignUpView)
    view.children = [MagicMock()]
    return view

@pytest.fixture
def mock_common_scripts():
    common_scripts = MagicMock()
    common_scripts.get_ksu_logo = AsyncMock(return_value="mock_logo_path")
    common_scripts.ksu_img_resize = AsyncMock(return_value=("mock_resized_logo", ".png"))
    return common_scripts

@pytest.fixture
def events_controller(mock_bot, mock_sign_up_view, mock_common_scripts):
    controller = EventsController(mock_bot)
    controller.SignUpView = mock_sign_up_view
    controller.common_scripts = mock_common_scripts
    return controller

@pytest.mark.asyncio
async def test_on_member_join_new_member(events_controller, mock_member, mock_db, mock_sign_up_view, mock_common_scripts):
    # Arrange
    mock_is_member_exist = mock_db.Player.isMemberExist.return_value = False
    mock_sign_up_view.children = [MagicMock()]  # Simulate that the view is active
    mock_sign_up_view.wait = AsyncMock()  # Mock the wait function to complete immediately
    mock_member.send = AsyncMock()  # Mock member's send method

    # Act
    await events_controller.on_member_join(mock_member)

    # Assert
    mock_member.send.assert_called_once()  # Check if send was called
    mock_sign_up_view.wait.assert_called_once()  # Ensure that the view waited for interaction
    mock_common_scripts.ksu_img_resize.assert_called_once_with("mock_logo_path")
    mock_common_scripts.get_ksu_logo.assert_called_once()
    assert mock_member.send.call_args[0][0].title == "Welcome to Test Guild server"  # Check the embed title

@pytest.mark.asyncio
async def test_on_member_join_existing_member(events_controller, mock_member, mock_db):
    # Arrange
    mock_is_member_exist = mock_db.Player.isMemberExist.return_value = True  # Simulate that the member exists

    # Act
    await events_controller.on_member_join(mock_member)

    # Assert
    mock_is_member_exist.assert_called_once()  # Ensure the check for member existence was made
    mock_member.send.assert_not_called()  # The member shouldn't receive any message if they already exist
'''