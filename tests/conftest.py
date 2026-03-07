"""
Pytest configuration for StegHunter tests
"""
import warnings
import numpy as np

def pytest_configure():
    """Configure pytest to suppress warnings"""
    # Suppress numpy runtime warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    warnings.filterwarnings('ignore', message='invalid value encountered in divide')
    warnings.filterwarnings('ignore', message='divide by zero encountered in divide')
    
    # Suppress numpy divide warnings
    np.seterr(divide='ignore', invalid='ignore')
