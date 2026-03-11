"""
CLI Test for Hybrid Steganalysis System
Tests all components: traditional ML, XGBoost, and deep learning
"""
import time
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from src.core.ensemble_steganalysis import HybridSteganalysisSystem
from src.core.ml_classifier import MLSteganalysisClassifier
import os

def create_sample_data():
    """Create sample training data for testing"""
    # In a real scenario, we'd use real images
    print("Creating sample training data...")
    
    # Create directory structure
    data_dir = Path("test_data")
    clean_dir = data_dir / "clean"
    stego_dir = data_dir / "stego"
    
    clean_dir.mkdir(parents=True, exist_ok=True)
    stego_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate sample images
    try:
        from PIL import Image
        import random
        
        # Generate 20 clean images
        for i in range(20):
            img = Image.new('RGB', (100, 100), color=(random.randint(0, 255), 
                                                 random.randint(0, 255), 
                                                 random.randint(0, 255)))
            img.save(clean_dir / f"clean_{i}.png")
        
        # Generate 20 stego images (simulated)
        for i in range(20):
            img = Image.new('RGB', (100, 100), color=(random.randint(0, 255), 
                                                 random.randint(0, 255), 
                                                 random.randint(0, 255)))
            img.save(stego_dir / f"stego_{i}.png")
        
        print(f"Created sample data at {data_dir}")
        return clean_dir, stego_dir
    except ImportError:
        print("PIL not available. Test data creation skipped.")
        return clean_dir, stego_dir

def test_hybrid_system():
    """Test the hybrid steganalysis system through CLI"""
    print("=" * 80)
    print("HYBRID STEGANALYSIS SYSTEM TEST")
    print("=" * 80)
    
    try:
        # Create sample data
        clean_dir, stego_dir = create_sample_data()
        
        # Initialize hybrid system
        print("\nInitializing hybrid steganalysis system...")
        hybrid = HybridSteganalysisSystem()
        
        # Train the model
        print("\nTraining hybrid model...")
        train_start = time.time()
        metrics = hybrid.train(
            clean_images=[str(p) for p in clean_dir.glob("*.png")],
            stego_images=[str(p) for p in stego_dir.glob("*.png")],
            model_save_path="test_models/hybrid_model",
            test_size=0.2
        )
        train_time = time.time() - train_start
        
        # Display training results
        print("\n" + "=" * 30 + " TRAINING RESULTS " + "=" * 30)
        print(f"Training time: {train_time:.2f} seconds")
        
        # Print component metrics
        for model_type in ['traditional_ensemble', 'xgboost', 'cnn']:
            if model_type in metrics and metrics[model_type]:
                print(f"\n{model_type.replace('_', ' ').title()} Results:")
                if 'error' in metrics[model_type]:
                    print(f"  Error: {metrics[model_type]['error']}")
                else:
                    print(f"  Accuracy: {metrics[model_type].get('accuracy', 0):.4f}")
                    print(f"  Precision: {metrics[model_type].get('precision', 0):.4f}")
                    print(f"  Recall: {metrics[model_type].get('recall', 0):.4f}")
                    print(f"  F1-Score: {metrics[model_type].get('f1_score', 0):.4f}")
        
        # Test with individual images
        print("\n" + "=" * 30 + " PREDICTION TESTS " + "=" * 30)
        
        # Test with a clean image
        clean_image = next(clean_dir.glob("*.png"), None)
        if clean_image:
            print(f"\nTesting with clean image: {clean_image.name}")
            results = hybrid.predict(str(clean_image))
            
            print(f"Traditional ML: {results.get('traditional', {}).get('prediction', 'N/A')} (Confidence: {results.get('traditional', {}).get('confidence', 0):.2f})")
            print(f"XGBoost: {results.get('xgboost', {}).get('prediction', 'N/A')} (Confidence: {results.get('xgboost', {}).get('confidence', 0):.2f})")
            print(f"CNN: {results.get('cnn', {}).get('prediction', 'N/A')} (Confidence: {results.get('cnn', {}).get('confidence', 0):.2f})")
            print(f"Final Result: {results.get('final', {}).get('prediction', 'N/A')} (Confidence: {results.get('final', {}).get('confidence', 0):.2f})")
        
        # Test with a stego image
        stego_image = next(stego_dir.glob("*.png"), None)
        if stego_image:
            print(f"\nTesting with stego image: {stego_image.name}")
            results = hybrid.predict(str(stego_image))
            
            print(f"Traditional ML: {results.get('traditional', {}).get('prediction', 'N/A')} (Confidence: {results.get('traditional', {}).get('confidence', 0):.2f})")
            print(f"XGBoost: {results.get('xgboost', {}).get('prediction', 'N/A')} (Confidence: {results.get('xgboost', {}).get('confidence', 0):.2f})")
            print(f"CNN: {results.get('cnn', {}).get('prediction', 'N/A')} (Confidence: {results.get('cnn', {}).get('confidence', 0):.2f})")
            print(f"Final Result: {results.get('final', {}).get('prediction', 'N/A')} (Confidence: {results.get('final', {}).get('confidence', 0):.2f})")
        
        # Generate performance report
        print("\n" + "=" * 30 + " PERFORMANCE REPORT " + "=" * 30)
        
        # Create visualization of results
        try:
            plt.figure(figsize=(10, 6))
            
            # Extract metrics
            models = []
            accuracies = []
            
            for model_type in ['traditional_ensemble', 'xgboost', 'cnn']:
                if model_type in metrics and metrics[model_type]:
                    models.append(model_type.replace('_', ' ').title())
                    accuracies.append(metrics[model_type].get('accuracy', 0) * 100)
            
            # Create bar chart
            plt.bar(models, accuracies, color=['#ff9999', '#66b3ff', '#99ff99'])
            plt.title('Model Accuracy Comparison')
            plt.ylabel('Accuracy (%)')
            plt.ylim(0, 100)
            
            # Add value labels on bars
            for i, v in enumerate(accuracies):
                plt.text(i, v + 1, f'{v:.1f}%', ha='center')
            
            plt.tight_layout()
            plt.savefig('hybrid_performance.png')
            
            print("Performance visualization saved as 'hybrid_performance.png'")
            print("\nTo view the report, check the generated 'hybrid_performance.png' file")
        
        except Exception as e:
            print(f"Error creating visualization: {e}")
        
        # Save detailed results to file
        with open('hybrid_test_results.json', 'w') as f:
            json.dump({
                'metrics': metrics,
                'training_time': train_time,
                'test_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        
        print("\nDetailed test results saved to 'hybrid_test_results.json'")
        
        # Cleanup
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Create test models directory
    Path("test_models").mkdir(exist_ok=True)
    
    try:
        test_hybrid_system()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
