from PIL import Image
import time
from pathlib import Path
from .lsb_analyzer import lsb_analysis
from .statistical_tests import chi_square_test, pixel_value_differencing

class SteganographyAnalyzer:
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def basic_analysis(self, image_path):
        """Basic file analysis (size vs dimensions)"""
        start_time = time.time()
        path = Path(image_path)
        image = Image.open(image_path)
        
        file_size = path.stat().st_size
        dimensions = (image.width, image.height)
        expected_size = dimensions[0] * dimensions[1] * len(image.mode)
        size_ratio = file_size / expected_size if expected_size > 0 else 0
        
        # Suspicion if size ratio is unusual
        suspicion_score = max(0, min(100, abs(size_ratio - 0.1) * 1000))
        
        results = {
            'filename': path.name,
            'file_size': file_size,
            'dimensions': dimensions,
            'format': image.format,
            'analysis_time': round(time.time() - start_time, 2),
            'size_ratio': size_ratio,
            'basic_suspicion_score': suspicion_score
        }
        return results

    def analyze_image(self, image_path):
        """Comprehensive analysis using multiple methods"""
        start_time = time.time()
        path = Path(image_path)
        image = Image.open(image_path)
        
        results = {
            'filename': path.name,
            'full_path': str(path),
            'file_size': path.stat().st_size,
            'format': image.format,
            'dimensions': (image.width, image.height),
            'mode': image.mode,
            'analysis_time': 0,
            'methods': {}
        }
        
        # Basic analysis
        results['methods']['basic'] = self.basic_analysis(image_path)
        
        # LSB analysis
        results['methods']['lsb'] = lsb_analysis(image)
        
        # Statistical tests
        results['methods']['chi_square'] = chi_square_test(image)
        results['methods']['pixel_differencing'] = pixel_value_differencing(image)
        
        # Combine scores
        scores = [
            results['methods']['basic']['basic_suspicion_score'],
            results['methods']['lsb']['lsb_suspicion_score'],
            results['methods']['pixel_differencing']['suspicion_score']
        ]
        avg_score = sum(scores) / len(scores) if scores else 0
        results['final_suspicion_score'] = round(avg_score, 2)
        
        results['analysis_time'] = round(time.time() - start_time, 2)
        
        return results
