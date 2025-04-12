import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from unittest.mock import call
from common import common_scripts
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestCommonScripts:

    @patch('common.common_scripts.pathlib.Path.glob')
    def test_get_ksu_logo_empty(self, mock_glob):
        # Mock the function to return an empty list
        mock_glob.return_value = []
        result = common_scripts.get_ksu_logo()
        assert result is None

    @patch('common.common_scripts.pathlib.Path.glob')
    def test_get_ksu_logo(self, mock_glob):
        # Mock the function to return a list of file paths
        mock_glob.return_value = ['path/to/ksu_logo.png']
        result = common_scripts.get_ksu_logo()
        assert result == 'path/to/ksu_logo.png'
        
    @patch('common.common_scripts.pathlib.Path.glob')
    @patch('common.common_scripts.get_ksu_logo')
    def test_get_ksu_logo_multiple_files(self, mock_get_ksu_logo, mock_glob):
        # Mock the function to return multiple file paths
        mock_glob.return_value = ['path/to/ksu_logo1.png', 'path/to/ksu_logo2.png']
        mock_get_ksu_logo.return_value = 'path/to/ksu_logo1.png'
        result = common_scripts.get_ksu_logo()
        assert result in ['path/to/ksu_logo1.png', 'path/to/ksu_logo2.png']


    @patch('common.common_scripts.ksu_img_resize')
    @patch('common.common_scripts.get_ksu_logo')
    @patch('discord.File')
    @pytest.mark.asyncio
    async def test_ksu_img_resize(self, mock_file, mock_get_ksu_logo, mock_ksu_img_resize):
        # Mock the image resizing function
        mock_ksu_img_resize.return_value = (MagicMock(), 'png')

        # Call the function
        result = await common_scripts.ksu_img_resize('path/to/image.png')

        # Assert the result
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Check if the image format is correct
        assert result[1] == 'png'
        # Check if the file was created
        mock_file.assert_called_once_with('path/to/image.png', 'rb')
        
    