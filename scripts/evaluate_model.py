"""
Evaluate ML model performance on test dataset
"""
import sys
import json
from pathlib import Path
import numpy as np
from src.core.ml_classifier import MLSteganalysisClassifier
from tabulate import tabulate

def evaluate_model(model_path: str, test_dir: str, true_labels: dict = None):
    """
    Evaluate model on test dataset
    Args:
        model_path: Path to trained model
        test_dir: Directory containing test images
        true_labels: Dictionary mapping filename to true label (0=clean, 1=stego)
    """
    # Load model
    classifier = MLSteganalysisClassifier(model_path)
    
    # Get test images
    supported = {'.jpg', '.jpeg', '.png', '.bmp'}
    test_images = [p for p in Path(test_dir).rglob('*') if p.is_file() and p.suffix.lower() in supported]
    
    if len(test_images) == 0:
        print(f"No test images found in {test_dir}")
        return
    
    print(f"Evaluating model on {len(test_images)} test images...")
    
    # Get predictions
    results = []
    for img_path in test_images:
        result = classifier.predict(str(img_path))
        results.append({
            'filename': img_path.name,
            'prediction': result['prediction'],
            'probability': result['probability'],
            'confidence': result['confidence']
        })
    
    # Calculate metrics if true labels provided
    if true_labels:
        y_true = []
        y_pred = []
        probabilities = []
        
        for result in results:
            filename = result['filename']
            if filename in true_labels:
                y_true.append(true_labels[filename])
                y_pred.append(result['prediction'])
                probabilities.append(result['probability'])
        
        if len(y_true) > 0:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
            
            metrics = {
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_score(y_true, y_pred, zero_division=0),
                'recall': recall_score(y_true, y_pred, zero_division=0),
                'f1_score': f1_score(y_true, y_pred, zero_division=0),
                'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
            }
            
            if len(set(y_true)) == 2:
                try:
                    metrics['auc_roc'] = roc_auc_score(y_true, probabilities)
                except:
                    metrics['auc_roc'] = 0.0
            
            print("\n" + "=" * 60)
            print("Evaluation Metrics")
            print("=" * 60)
            print(f"Accuracy:  {metrics['accuracy']:.4f}")
            print(f"Precision: {metrics['precision']:.4f}")
            print(f"Recall:    {metrics['recall']:.4f}")
            print(f"F1-Score:  {metrics['f1_score']:.4f}")
            if 'auc_roc' in metrics:
                print(f"AUC-ROC:   {metrics['auc_roc']:.4f}")
            
            print("\nConfusion Matrix:")
            print(f"           Predicted: Clean  Stego")
            print(f"True:Clean   {metrics['confusion_matrix'][0][0]:6d}  {metrics['confusion_matrix'][0][1]:6d}")
            print(f"     Stego    {metrics['confusion_matrix'][1][0]:6d}  {metrics['confusion_matrix'][1][1]:6d}")
            
            return metrics
    
    # Display prediction summary
    print("\nPrediction Summary:")
    summary_data = []
    for result in results:
        pred_text = "STEGO" if result['prediction'] == 1 else "CLEAN"
        summary_data.append([
            result['filename'],
            pred_text,
            f"{result['probability']:.4f}",
            f"{result['confidence']:.4f}"
        ])
    
    headers = ["Filename", "Prediction", "Probability", "Confidence"]
    print(tabulate(summary_data, headers=headers, tablefmt="grid"))

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 2:
        print("Usage: python evaluate_model.py <model_path> <test_dir> [labels_file]")
        print("Example: python evaluate_model.py models/steg_model.pkl test_images labels.json")
        sys.exit(1)
    
    model_path = sys.argv[1]
    test_dir = sys.argv[2]
    
    true_labels = None
    if len(sys.argv) > 3:
        with open(sys.argv[3], 'r') as f:
            true_labels = json.load(f)
    
    evaluate_model(model_path, test_dir, true_labels)

if __name__ == '__main__':
    main()
