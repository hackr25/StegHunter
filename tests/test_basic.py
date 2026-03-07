import unittest
import os
from pathlib import Path
from click.testing import CliRunner
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from steg_hunter_cli import cli

class TestStegHunterWeek2(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = Path("test_images")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test image
        from PIL import Image
        self.test_image_path = self.test_dir / "test_week2.png"
        img = Image.new('RGB', (100, 100), color='green')
        img.save(self.test_image_path)

    def tearDown(self):
        # Cleanup test files
        if self.test_image_path.exists():
            self.test_image_path.unlink()

    def test_info_command_success(self):
        """Test info command with a valid image"""
        result = self.runner.invoke(cli, ['info', str(self.test_image_path)])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Image Analysis', result.output)
        self.assertIn('test_week2.png', result.output)
        self.assertIn('Format', result.output)
        self.assertIn('Dimensions', result.output)

    def test_info_command_nonexistent_file(self):
        """Test error handling for non-existent files"""
        result = self.runner.invoke(cli, ['info', 'C:\\nonexistent\\file.jpg'])
        self.assertEqual(result.exit_code, 0)  # Error is caught and handled
        self.assertIn('not found', result.output.lower())

    def test_analyze_command_single_file(self):
        """Test basic analysis functionality for single file"""
        result = self.runner.invoke(cli, ['analyze', str(self.test_image_path)])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Analyzing', result.output)
        self.assertIn('Final Suspicion Score', result.output)
        # Platform output removed in Week 2, so we don't check for it

    def test_analyze_command_verbose(self):
        """Test analyze command with verbose output"""
        result = self.runner.invoke(cli, ['analyze', str(self.test_image_path), '--verbose'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('filename', result.output)
        self.assertIn('methods', result.output)
        self.assertIn('lsb', result.output)

    def test_windows_path_handling(self):
        """Test various Windows path formats"""
        # Test relative path
        result = self.runner.invoke(cli, ['info', 'test_images/test_week2.png'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('test_week2.png', result.output)

if __name__ == '__main__':
    unittest.main()
