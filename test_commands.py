import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord import Interaction, Permissions
from controller.admin_controller import Admin_commands  
from controller.player_signup import PlayerSignUp 
from controller.player_commands import PlayerDetails
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, ANY


@pytest.fixture
def test_bot():
    return MagicMock()

@pytest.fixture
def admin_user():
    """Creates a mock user with administrator permissions."""
    user = MagicMock()
    user.guild_permissions = Permissions(administrator=True)
    return user

@pytest.fixture
def non_admin_user():
    """Creates a mock user without administrator permissions."""
    user = MagicMock()
    user.guild_permissions = Permissions(administrator=False)
    return user

@pytest.fixture
def mock_interaction(admin_user):
    """Creates a mock interaction with an admin user."""
    interaction = MagicMock(spec=Interaction)
    interaction.user = admin_user
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction

@pytest.fixture
def mock_interaction_non_admin(non_admin_user):
    """Creates a mock interaction with a non-admin user."""
    interaction = MagicMock(spec=Interaction)
    interaction.user = non_admin_user
    interaction.response.send_message = AsyncMock()
    return interaction

@pytest.mark.asyncio
async def test_checkin_admin(test_bot, mock_interaction):
    """Test that the /checkin_game command executes successfully for admins."""
    cog = Admin_commands(test_bot)

    with patch("controller.admin_controller.Details_Cached.get_channel_id", new=AsyncMock(return_value=123456)), \
         patch("controller.admin_controller.Checkin.createTable"), \
         patch("controller.admin_controller.CheckinView", return_value=MagicMock()), \
         patch.object(mock_interaction.guild, "get_channel", return_value=MagicMock(send=AsyncMock())):

        await cog.checkin.callback(cog, mock_interaction, timeout=60)

        mock_interaction.response.send_message.assert_called_with("Invitation successfully sent")
        mock_interaction.followup.send.assert_called_with("Check-In time has been completed")

@pytest.mark.asyncio
async def test_checkin_non_admin(test_bot, mock_interaction_non_admin):
    """Test that non-admins cannot execute the /checkin_game command."""
    cog = Admin_commands(test_bot)

    await cog.checkin.callback(cog, mock_interaction_non_admin, timeout=60)

    mock_interaction_non_admin.response.send_message.assert_called_with(
        "Sorry you dont have access to use this command", ephemeral=True
    )

@pytest.mark.asyncio
async def test_tier_update_admin(test_bot, mock_interaction):
    """Test /updatetier command for admins with a valid player ID."""
    cog = Admin_commands(test_bot)

    with patch("controller.admin_controller.Player_game_info.fetch_by_id", return_value=[("Gold",)]), \
         patch("controller.admin_controller.TierView", return_value=MagicMock()):

        await cog.tier_update.callback(cog, mock_interaction, player_id="123456")

        mock_interaction.response.send_message.assert_called_with(
            "player current tier is Gold select the tier from dropdown", view=ANY
        )

@pytest.mark.asyncio
async def test_tier_update_invalid_player(test_bot, mock_interaction):
    """Test /updatetier when an invalid player ID is given."""
    cog = Admin_commands(test_bot)

    with patch("controller.admin_controller.Player_game_info.fetch_by_id", return_value=None):
        await cog.tier_update.callback(cog, mock_interaction, player_id="999999")

        mock_interaction.response.send_message.assert_called_with(
            "Player not found, please check the user id"
        )

@pytest.mark.asyncio
async def test_tier_update_non_admin(test_bot, mock_interaction_non_admin):
    """Test that non-admins cannot use the /updatetier command."""
    cog = Admin_commands(test_bot)

    await cog.tier_update.callback(cog, mock_interaction_non_admin, player_id="valid_player")

    mock_interaction_non_admin.response.send_message.assert_called_with(
        "Sorry you dont have access to use this command", ephemeral=True
    )

@pytest.mark.asyncio
async def test_toxicity_update_admin(test_bot, mock_interaction):
    """Test the /toxicity command for admins when a valid player is found."""
    cog = Admin_commands(test_bot)

    with patch("controller.admin_controller.PlayerModel.update_toxicity", return_value=True):
        await cog.toxicity.callback(cog, mock_interaction, player="toxic_player")

        mock_interaction.response.send_message.assert_called_with(
            "toxic_player's toxicity point has been updated.", ephemeral=True
        )

@pytest.mark.asyncio
async def test_toxicity_update_invalid_player(test_bot, mock_interaction):
    """Test the /toxicity command when a player is not found."""
    cog = Admin_commands(test_bot)

    with patch("controller.admin_controller.PlayerModel.update_toxicity", return_value=False):
        await cog.toxicity.callback(cog, mock_interaction, player="unknown_player")

        mock_interaction.response.send_message.assert_called_with(
            "unknown_player , this username could not be found.", ephemeral=True
        )

@pytest.mark.asyncio
async def test_toxicity_update_non_admin(test_bot, mock_interaction_non_admin):
    """Test that non-admins cannot use the /toxicity command."""
    cog = Admin_commands(test_bot)

    await cog.toxicity.callback(cog, mock_interaction_non_admin, player="some_player")

    mock_interaction_non_admin.response.send_message.assert_called_with(
        "❌ This command is only for administrators.", ephemeral=True
    )

@pytest.mark.asyncio
@patch("controller.player_signup.SharedLogic.execute_signup_model", new_callable=AsyncMock)
async def test_player_signup_success(mock_execute, test_bot, mock_interaction):
    """Test the /register command runs successfully."""
    cog = PlayerSignUp(test_bot)

    await cog.player_signup.callback(cog, mock_interaction)

    mock_execute.assert_awaited_once_with(mock_interaction)



