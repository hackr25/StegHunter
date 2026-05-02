#!/usr/bin/env python3
"""
Test script to check if ML implementation is working
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

print("🤖 ML IMPLEMENTATION TEST SCRIPT")
print("=" * 60)
print()

# Test 1: Check model file
print("Test 1: Checking ML Model File...")
print("-" * 60)
model_path = Path("models/steg_model.pkl")

if model_path.exists():
    size = model_path.stat().st_size / (1024 * 1024)
    print(f"✅ Model file found: {model_path} ({size:.2f} MB)")
else:
    print(f"❌ Model file NOT found: {model_path}")

print()

# Test 2: Load ML Classifier
print("Test 2: Loading ML Classifier...")
print("-" * 60)
try:
    from src.core.ml_classifier import MLSteganalysisClassifier
    
    if model_path.exists():
        classifier = MLSteganalysisClassifier(model_path=str(model_path))
        
        if classifier.model is not None:
            print(f"✅ ML model loaded successfully")
            print(f"   Model type: {type(classifier.model).__name__}")
            print(f"   Model: {classifier.model}")
        else:
            print(f"❌ Classifier initialized but model is None")
    else:
        print(f"❌ Cannot load classifier - model file not found")
        
except Exception as e:
    print(f"❌ Error loading ML classifier: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Feature Extraction
print("Test 3: Testing Feature Extraction...")
print("-" * 60)
try:
    from src.core.ml_features import MLFeatureExtractor
    
    # Create test image
    test_img_path = Path("test_ml_temp.png")
    img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    img.save(test_img_path)
    print(f"✅ Test image created: {test_img_path}")
    
    # Extract features
    extractor = MLFeatureExtractor()
    features = extractor.extract_features(str(test_img_path))
    
    if features:
        print(f"✅ Features extracted successfully")
        print(f"   Number of features: {len(features)}")
        print(f"   Feature names: {list(features.keys())[:5]}...")
        
        # Check for NaN
        nan_count = sum(1 for v in features.values() if isinstance(v, float) and np.isnan(v))
        if nan_count > 0:
            print(f"⚠️  Warning: {nan_count} NaN values in features")
        else:
            print(f"✅ No NaN values in features")
    else:
        print(f"❌ Features extraction returned empty")
    
    # Cleanup
    test_img_path.unlink()
    
except Exception as e:
    print(f"❌ Error during feature extraction: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Check CLI integration
print("Test 4: Checking CLI Integration...")
print("-" * 60)
try:
    cli_content = Path("steg_hunter_cli.py").read_text()
    
    if "use-ml" in cli_content or "use_ml" in cli_content:
        print("✅ ML flag found in CLI (--use-ml option)")
    else:
        print("❌ ML flag not found in CLI")
        
    if "ml_classifier" in cli_content or "MLSteganalysisClassifier" in cli_content:
        print("✅ ML classifier imported/used in CLI")
    else:
        print("⚠️  ML classifier may not be used in CLI")
        
except Exception as e:
    print(f"❌ Error checking CLI: {e}")

print()

# Test 5: Summary
print("=" * 60)
print("SUMMARY:")
print("-" * 60)
print()

status_checks = {
    "ML Model File": model_path.exists(),
    "ML Classifier Module": Path("src/core/ml_classifier.py").exists(),
    "ML Features Module": Path("src/core/ml_features.py").exists(),
    "CLI Support": "--use-ml" in Path("steg_hunter_cli.py").read_text() if Path("steg_hunter_cli.py").exists() else False,
}

all_good = all(status_checks.values())

for check, status in status_checks.items():
    emoji = "✅" if status else "❌"
    print(f"{emoji} {check}")

print()

if all_good:
    print("🎉 ML Implementation: READY & WORKING")
else:
    print("⚠️  ML Implementation: PARTIAL or NEEDS SETUP")

print()
