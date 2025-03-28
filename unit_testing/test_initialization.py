import asyncio
import logging
import pytest
import tournament


@pytest.mark.asyncio()
async def test_start_bot(caplog):
    # Add a StreamHandler to the "discord" logger if it doesn't have one
    logger = tournament.settings.logging.getLogger("discord")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

    # Now set caplog to capture INFO-level messages for the "discord" logger.
    caplog.set_level("INFO", logger="discord")

    bot_task = asyncio.create_task(tournament.main())
    await asyncio.sleep(5)

    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

    print("Captured logs:", caplog.text)  # For debugging
    assert "Logged into server as" in caplog.text
