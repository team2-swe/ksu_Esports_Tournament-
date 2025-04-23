import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
import asyncio
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
    
    # Create a wait method that returns immediately without waiting
    async def immediate_return(*args, **kwargs):
        return None
    
    view.wait = immediate_return
    view.message = MagicMock()
    return view

@pytest.mark.asyncio
async def test_on_member_join_new_member(events_controller, mock_member, mock_db, mock_sign_up_view):
    # Create a no-op wait method to replace SignUpView.wait
    async def skip_wait(self):
        pass  # Do nothing and return immediately
    
    # Mocking discord.Embed and discord.File
    with patch('discord.Embed') as MockEmbed, \
         patch('discord.File') as MockFile, \
         patch('model.dbc_model.Tournament_DB', return_value=mock_db), \
         patch('model.dbc_model.Player.isMemberExist', return_value=False), \
         patch('view.signUp_view.SignUpView', return_value=mock_sign_up_view), \
         patch('common.common_scripts.get_ksu_logo', return_value='/common/images/KSU_Esports_Tournament.png'), \
         patch('common.common_scripts.ksu_img_resize', return_value=(MagicMock(), '.png')), \
         patch('asyncio.sleep', AsyncMock()), \
         patch('view.signUp_view.SignUpView.wait', skip_wait):
        
        # Create mock instances of Embed and File
        mock_embed_instance = MagicMock()
        mock_file_instance = MagicMock()
        
        # Set the mock return values
        MockEmbed.return_value = mock_embed_instance
        MockFile.return_value = mock_file_instance

        # Run the test
        await events_controller.on_member_join(mock_member)

        # Verify that the discord.Embed was created with the correct arguments
        MockEmbed.assert_called_once()
        embed_call_kwargs = MockEmbed.call_args.kwargs
        assert embed_call_kwargs['color'] == discord.Colour.dark_teal()
        assert "Please Register Here" in embed_call_kwargs['description']
        assert embed_call_kwargs['title'] == "Welcome To KSU eSports Server"

        # Verify that the discord.File was created with the right arguments
        # We don't check the exact MockFile parameters as we're using a MagicMock instance for the file
        assert MockFile.called

        # Verify that the member's send method was called with the mock embed and file
        mock_member.send.assert_any_call(embed=mock_embed_instance, file=mock_file_instance)
        mock_member.send.assert_any_call(view=mock_sign_up_view)

        # Assert that the embed has a thumbnail set with the correct URL
        mock_embed_instance.set_thumbnail.assert_called_once_with(url="attachment://resized_logo.png")
        
        # Verify that the view's wait method was called
        mock_sign_up_view.wait.assert_called_once()

@pytest.mark.asyncio
async def test_on_member_join_existing_member(events_controller, mock_member, mock_db):
    # Create a no-op wait method to replace SignUpView.wait
    async def skip_wait(self):
        pass  # Do nothing and return immediately
    
    with patch('model.dbc_model.Tournament_DB', return_value=mock_db), \
         patch('model.dbc_model.Player.isMemberExist', return_value=True), \
         patch('view.signUp_view.SignUpView.wait', skip_wait):
        
        # Run the test
        await events_controller.on_member_join(mock_member)
        
        # Verify that the database was checked and closed
        assert dbc_model.Player.isMemberExist.called_with(mock_db, mock_member.id)
        mock_db.close_db.assert_called_once()
        
        # Verify that no messages were sent (member already exists)
        mock_member.send.assert_not_called()

@pytest.mark.asyncio
async def test_on_member_join_view_no_children(events_controller, mock_member, mock_db):
    # Create a mock SignUpView with no children
    mock_sign_up_view = MagicMock(spec=SignUpView)
    mock_sign_up_view.children = False
    
    with patch('model.dbc_model.Tournament_DB', return_value=mock_db), \
         patch('model.dbc_model.Player.isMemberExist', return_value=False), \
         patch('view.signUp_view.SignUpView', return_value=mock_sign_up_view):
        
        # Mock the guild owner
        mock_guild_owner = MagicMock()
        mock_guild_owner.send = AsyncMock()
        mock_member.guild.owner = mock_guild_owner
        
        # Run the test
        await events_controller.on_member_join(mock_member)
        
        # Verify that the server owner was notified
        mock_guild_owner.send.assert_called_once()
        # Check that the error message is present in the notification
        assert "signup view is not working" in mock_guild_owner.send.call_args.args[0]

@pytest.mark.asyncio
async def test_on_member_remove(events_controller, mock_member, mock_db):
    with patch('model.dbc_model.Tournament_DB', return_value=mock_db), \
         patch('model.dbc_model.Player.remove_player') as mock_remove_player:
        
        # Run the test
        await events_controller.on_member_remove(mock_member)
        
        # Verify that the player was removed from the database
        mock_remove_player.assert_called_once_with(mock_db, mock_member.id)
        mock_db.close_db.assert_called_once()