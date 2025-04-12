import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import unittest
from unittest.mock import mock_open, patch, MagicMock, call
import pytest
import json
import discord
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.cached_details import Details_Cached


class TestDetailsCached(unittest.TestCase):

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"123": [{"channel_name": 1}]}')
    @pytest.mark.asyncio
    async def test_load_cache_success(self, mock_open, mock_exists):
        mock_exists.return_value = True
        result = await Details_Cached.load_cache()
        expected_result = {"123": [{"channel_name": 1}]}
        self.assertEqual(result, expected_result)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @pytest.mark.asyncio
    async def test_load_cache_failure(self, mock_open, mock_exists):
        mock_exists.return_value = False
        result = await Details_Cached.load_cache()
        self.assertEqual(result, {})

    @patch('builtins.open', new_callable=mock_open)
    @pytest.mark.asyncio
    def test_save_cache(self, mock_file):
        data = {"123": [{"channel_name": 1}]}
        Details_Cached.save_cache(data)
        # The expected JSON content broken into chunks as `json.dump()` would write it
        expected_calls = [
            call('{'),
            call('"123"'),
            call(': '),
            call('['),
            call('{'),
            call('"channel_name"'),
            call(': '),
            call('1'),
            call('}'),
            call(']'),
            call('}')
        ]
        
        # Check that write was called with each part of the expected JSON string
        mock_file().write.assert_has_calls(expected_calls)
        self.assertEqual(mock_file().write.call_count, len(expected_calls))

    @patch('discord.utils.get')
    @patch('common.cached_details.Details_Cached.load_cache', return_value={"123": [{"channel_name": 1}]})
    @pytest.mark.asyncio
    async def test_get_channel_id_found(self, mock_load_cache, mock_get):
        mock_get.return_value = MagicMock(id=1)
        channel_id = await Details_Cached.get_channel_id("channel_name", 123)
        self.assertEqual(channel_id, 1)

    @patch('discord.utils.get')
    @patch('common.cached_details.Details_Cached.load_cache', return_value={"123": [{"channel_name": 1}]})
    async def test_get_channel_id_not_found(self, mock_load_cache, mock_get):
        mock_get.return_value = None
        channel_id = await Details_Cached.get_channel_id("nonexistent_channel", 123)
        self.assertIsNone(channel_id)

    @patch('discord.utils.get')
    @patch('common.cached_details.Details_Cached.load_cache', return_value={"123": [{"channel_name": 1}]})
    @pytest.mark.asyncio
    async def test_isChannelNotCreated_false(self, mock_load_cache, mock_get):
        mock_get.return_value = MagicMock(id=1)
        result = await Details_Cached.isChannelNotCreated(None, MagicMock(id=123), {"123": [{"channel_name": 1}]})
        self.assertFalse(result)

    @patch('discord.utils.get')
    @patch('common.cached_details.Details_Cached.load_cache', return_value={})
    @pytest.mark.asyncio
    async def test_isChannelNotCreated_true(self, mock_load_cache, mock_get):
        result = await Details_Cached.isChannelNotCreated(None, MagicMock(id=123), {})
        self.assertTrue(result)

    @patch('discord.utils.get')
    @patch('common.cached_details.Details_Cached.load_cache', return_value={})
    @pytest.mark.asyncio
    async def test_channels_for_tournament(self, mock_load_cache, mock_get):
        mock_get.return_value = MagicMock(id=1)
        mock_guild = MagicMock()
        mock_guild.id = 123

        ch_config = json.dumps({
            "Category1": {
                "channel_name": ["role1"]
            }
        })

        await Details_Cached.channels_for_tournament(ch_config, mock_guild)
        
        mock_guild.create_category.assert_called_once_with("Category1")
        mock_guild.create_text_channel.assert_called()

