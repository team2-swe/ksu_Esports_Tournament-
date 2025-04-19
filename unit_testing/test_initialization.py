import asyncio
import logging
import pytest
import tournament


@pytest.mark.asyncio()
async def test_start_bot(caplog, monkeypatch):
    # Mock the bot start to avoid actual login
    async def mock_bot_start(*args, **kwargs):
        logger = tournament.settings.logging.getLogger("discord")
        logger.info("Logged into server as MockBot")
        return
        
    # Patch the bot's start method
    monkeypatch.setattr("discord.ext.commands.Bot.start", mock_bot_start)
    
    # Add a StreamHandler to the "discord" logger if it doesn't have one
    logger = tournament.settings.logging.getLogger("discord")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

    # Now set caplog to capture INFO-level messages for the "discord" logger.
    caplog.set_level(logging.INFO, logger="discord")

    # Start the bot with mocked functions
    bot_task = asyncio.create_task(tournament.main())
    await asyncio.sleep(1)  # Reduced sleep time since we're mocking

    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

    print("Captured logs:", caplog.text)  # For debugging
    assert "Logged into server as" in caplog.text
