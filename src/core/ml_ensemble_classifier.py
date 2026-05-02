"""
Ensemble ML model combining Random Forest, XGBoost, and SVM
Provides maximum accuracy through voting and weighted averaging
"""

import os
import pickle
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')


class EnsembleMLClassifier:
    """
    Ensemble classifier combining Random Forest, XGBoost, and SVM.
    
    Advantages:
    - Combines strengths of all three algorithms
    - Reduces individual model biases
    - Superior accuracy (typically 3-7% better than single models)
    - More robust to different data distributions
    - Weighted voting can prioritize high-accuracy models
    """
    
    def __init__(self, model_path=None, weights=None):
        """
        Initialize ensemble classifier
        
        Args:
            model_path (str): Path to save/load ensemble model
            weights (list): Weights for voting [rf_weight, xgb_weight, svm_weight]
                           Default: [0.3, 0.4, 0.3] (XGBoost gets more weight)
        """
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path or os.path.join(
            Path(__file__).parent.parent.parent,
            "models",
            "steg_model_ensemble.pkl"
        )
        
        # Default weights: XGBoost gets slightly more weight as it typically performs best
        self.weights = weights or [0.3, 0.4, 0.3]
        
        # Load pre-trained model if available
        if os.path.exists(self.model_path):
            try:
                self.load_model()
            except Exception:
                pass  # Model will be created when train() is called
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train ensemble of Random Forest, XGBoost, and SVM
        
        Args:
            X_train (np.ndarray): Training features
            y_train (np.ndarray): Training labels
            X_val (np.ndarray): Validation features
            y_val (np.ndarray): Validation labels
            
        Returns:
            dict: Training metrics for the ensemble
        """
        # Import here to avoid circular imports
        from src.core.ml_rf_classifier import RandomForestClassifier
        from src.core.ml_xgboost_classifier import XGBoostClassifier
        from src.core.ml_svm_classifier import SVMClassifier
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Initialize individual classifiers
        rf_clf = RandomForestClassifier()
        xgb_clf = XGBoostClassifier()
        svm_clf = SVMClassifier()
        
        # Train individual models
        print("  Training Random Forest...")
        rf_metrics = rf_clf.train(X_train, y_train, X_val, y_val)
        
        print("  Training XGBoost...")
        xgb_metrics = xgb_clf.train(X_train, y_train, X_val, y_val)
        
        print("  Training SVM...")
        svm_metrics = svm_clf.train(X_train, y_train, X_val, y_val)
        
        # Create voting ensemble
        self.model = VotingClassifier(
            estimators=[
                ('rf', rf_clf.model),
                ('xgb', xgb_clf.model),
                ('svm', svm_clf.model)
            ],
            voting='soft',  # Soft voting using probability estimates
            weights=self.weights
        )
        
        # Train the ensemble
        self.model.fit(X_train_scaled, y_train)
        
        # Predict with ensemble
        y_pred_train = self.model.predict(X_train_scaled)
        
        metrics = {
            'accuracy': accuracy_score(y_train, y_pred_train),
            'precision': precision_score(y_train, y_pred_train, zero_division=0),
            'recall': recall_score(y_train, y_pred_train, zero_division=0),
            'f1': f1_score(y_train, y_pred_train, zero_division=0),
            'rf_f1': rf_metrics['f1'],
            'xgb_f1': xgb_metrics['f1'],
            'svm_f1': svm_metrics['f1']
        }
        
        # Validation metrics
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            y_pred_val = self.model.predict(X_val_scaled)
            metrics['val_accuracy'] = accuracy_score(y_val, y_pred_val)
            metrics['val_f1'] = f1_score(y_val, y_pred_val, zero_division=0)
        
        return metrics
    
    def predict(self, X):
        """
        Predict with ensemble (soft voting)
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            np.ndarray: Predictions (0=Clean, 1=Stego)
        """
        if self.model is None:
            raise RuntimeError("Ensemble not trained or loaded")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """
        Get probability predictions from ensemble
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            np.ndarray: Probability estimates [[clean_prob, stego_prob], ...]
        """
        if self.model is None:
            raise RuntimeError("Ensemble not trained or loaded")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_confidence(self, X):
        """
        Get confidence scores
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            np.ndarray: Confidence scores (0-1)
        """
        proba = self.predict_proba(X)
        return np.max(proba, axis=1)
    
    def get_individual_predictions(self, X):
        """
        Get predictions from each base classifier
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            dict: Predictions from each model
        """
        if self.model is None:
            raise RuntimeError("Ensemble not trained or loaded")
        
        X_scaled = self.scaler.transform(X)
        
        predictions = {}
        # Access base estimators using named_estimators_
        for name, estimator in self.model.named_estimators_.items():
            try:
                predictions[f'{name}_pred'] = estimator.predict(X_scaled)
                if hasattr(estimator, 'predict_proba'):
                    proba = estimator.predict_proba(X_scaled)
                    predictions[f'{name}_confidence'] = np.max(proba, axis=1)
            except Exception as e:
                predictions[f'{name}_error'] = str(e)
        
        return predictions
    
    def get_model_weights(self):
        """Get the weights assigned to each base classifier"""
        return {
            'random_forest': self.weights[0],
            'xgboost': self.weights[1],
            'svm': self.weights[2]
        }
    
    def set_model_weights(self, weights):
        """
        Adjust weights for voting
        
        Args:
            weights (list): New weights [rf, xgb, svm] (should sum to 1.0)
        """
        if sum(weights) > 1.01 or sum(weights) < 0.99:
            print(f"Warning: Weights don't sum to 1.0, normalizing...")
            weights = np.array(weights) / sum(weights)
        
        self.weights = weights
        if self.model is not None:
            self.model.weights = weights
    
    def save_model(self, path=None):
        """Save ensemble model"""
        path = path or self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'weights': self.weights
            }, f)
    
    def load_model(self, path=None):
        """Load pre-trained ensemble model"""
        path = path or self.model_path
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Ensemble model file not found: {path}")
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.weights = data.get('weights', [0.3, 0.4, 0.3])


class VotingStrategy:
    """Helper class for ensemble voting strategies"""
    
    @staticmethod
    def hard_voting(predictions):
        """
        Hard voting (majority vote)
        
        Args:
            predictions (dict): Individual model predictions
            
        Returns:
            int: Most common prediction
        """
        votes = [
            predictions.get('rf_pred'),
            predictions.get('xgb_pred'),
            predictions.get('svm_pred')
        ]
        votes = [v for v in votes if v is not None]
        return max(set(votes), key=votes.count)
    
    @staticmethod
    def weighted_voting(predictions, confidences, weights=None):
        """
        Weighted voting based on confidence scores
        
        Args:
            predictions (dict): Individual model predictions
            confidences (dict): Confidence scores for each model
            weights (list): Optional weights for models
            
        Returns:
            int: Prediction based on weighted confidence
        """
        if weights is None:
            weights = [0.3, 0.4, 0.3]  # Default: RF, XGB, SVM
        
        models = ['rf', 'xgb', 'svm']
        weighted_score = 0.0
        total_weight = 0.0
        
        for i, model in enumerate(models):
            pred_key = f'{model}_pred'
            conf_key = f'{model}_confidence'
            
            if pred_key in predictions and conf_key in confidences:
                pred = predictions[pred_key]
                conf = confidences[conf_key]
                weighted_score += (pred * conf * weights[i])
                total_weight += (conf * weights[i])
        
        return 1 if weighted_score > (total_weight * 0.5) else 0
