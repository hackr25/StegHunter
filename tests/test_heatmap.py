import unittest
from pathlib import Path
from src.core.heatmap_generator import HeatmapGenerator
from PIL import Image
import numpy as np

class TestHeatmapGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = HeatmapGenerator()
        self.test_dir = Path("test_images")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create test image
        self.test_image_path = self.test_dir / "test_heatmap.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(self.test_image_path)
        
        self.output_path = self.test_dir / "heatmap_output.png"
    
    def tearDown(self):
        # Clean up output files
        if self.output_path.exists():
            self.output_path.unlink()
        if self.test_image_path.exists():
            self.test_image_path.unlink()
    
    def test_lsb_heatmap_generation(self):
        """Test LSB heatmap generation"""
        heatmap = self.generator.generate_lsb_heatmap(self.test_image_path, self.output_path)
        
        # Check that heatmap was created
        self.assertTrue(self.output_path.exists())
        
        # Check heatmap properties
        self.assertIsInstance(heatmap, np.ndarray)
        self.assertEqual(len(heatmap.shape), 3)  # Color image
    
    def test_heatmap_shape(self):
        """Test that heatmap has correct shape"""
        heatmap = self.generator.generate_lsb_heatmap(self.test_image_path)
        
        # Load original image
        original = Image.open(self.test_image_path)
        original_array = np.array(original)
        
        # Check dimensions
        self.assertEqual(heatmap.shape[0], original_array.shape[0])
        self.assertEqual(heatmap.shape[1], original_array.shape[1])
        self.assertEqual(heatmap.shape[2], 3)  # RGB
    
    def test_comprehensive_heatmap(self):
        """Test comprehensive heatmap generation"""
        heatmaps = self.generator.generate_comprehensive_heatmap(
            self.test_image_path, 
            self.output_path
        )
        
        # Check that different heatmaps were generated
        self.assertIn('lsb', heatmaps)
        self.assertIn('variance', heatmaps)
        self.assertIn('edge', heatmaps)
        self.assertIn('combined', heatmaps)
        
        # Check that output file was created
        self.assertTrue(self.output_path.exists())

if __name__ == '__main__':
    unittest.main()
