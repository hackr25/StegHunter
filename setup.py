"""
Setup configuration for StegHunter CLI tool.

Enables installation as a system command: steg-hunter
"""

from setuptools import setup, find_packages

setup(
    name="steg-hunter",
    version="2.0.0",
    description="Advanced Steganography & Forensics Detection Suite",
    author="StegHunter Team",
    author_email="info@steghunter.dev",
    url="https://github.com/hackr25/StegHunter",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "Pillow>=9.0.0",
        "scikit-learn>=1.3.0",
        "xgboost>=2.0.0",
        "opencv-python>=4.8.0",
        "PyYAML>=6.0",
        "piexif>=1.1.3",
        "watchdog>=6.0.0",
        "imageio[ffmpeg]>=2.37.0",
        "click>=8.0.0",
        "tqdm>=4.60.0",
        "rich>=13.0.0",
        "PyQt5>=5.15.0",
        "reportlab>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "steg-hunter=steg_hunter_cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Security",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Multimedia :: Video",
    ],
    keywords="steganography forensics detection security image video analysis",
)
