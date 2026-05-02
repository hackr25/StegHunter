"""
Random Forest-based steganography classifier (consistent with XGBoost and SVM interfaces)
"""

import os
import pickle
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier as RFSKL
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class RandomForestClassifier:
    """
    Random Forest classifier for steganography detection.
    Wrapper around sklearn's RandomForestClassifier with consistent interface
    matching XGBoost and SVM classifiers.
    """
    
    def __init__(self, model_path=None):
        """
        Initialize Random Forest classifier
        
        Args:
            model_path (str): Path to pre-trained model file
        """
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path or os.path.join(
            Path(__file__).parent.parent.parent,
            "models",
            "steg_model.pkl"
        )
        
        # Load pre-trained model if available (with error handling for incompatible formats)
        if os.path.exists(self.model_path):
            try:
                self.load_model()
            except Exception as e:
                # If loading fails, initialize fresh model
                self._initialize_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new Random Forest model with optimal hyperparameters"""
        self.model = RFSKL(
            n_estimators=100,         # Number of trees
            max_depth=10,             # Maximum depth
            min_samples_split=5,      # Minimum samples to split
            min_samples_leaf=2,       # Minimum samples in leaf
            random_state=42,
            n_jobs=-1,                # Use all CPU cores
            class_weight='balanced'   # Handle class imbalance
        )
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train Random Forest classifier
        
        Args:
            X_train (np.ndarray): Training features (n_samples, n_features)
            y_train (np.ndarray): Training labels (0=Clean, 1=Stego)
            X_val (np.ndarray): Validation features
            y_val (np.ndarray): Validation labels
            
        Returns:
            dict: Training metrics including accuracy, precision, recall, F1
        """
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train Random Forest
        self.model.fit(X_train_scaled, y_train)
        
        # Calculate training metrics
        y_pred_train = self.model.predict(X_train_scaled)
        metrics = {
            'accuracy': accuracy_score(y_train, y_pred_train),
            'precision': precision_score(y_train, y_pred_train, zero_division=0),
            'recall': recall_score(y_train, y_pred_train, zero_division=0),
            'f1': f1_score(y_train, y_pred_train, zero_division=0)
        }
        
        # Validation metrics if provided
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            y_pred_val = self.model.predict(X_val_scaled)
            metrics['val_accuracy'] = accuracy_score(y_val, y_pred_val)
            metrics['val_f1'] = f1_score(y_val, y_pred_val, zero_division=0)
        
        return metrics
    
    def predict(self, X):
        """
        Predict if images are clean or stego
        
        Args:
            X (np.ndarray): Features array (n_samples, n_features)
            
        Returns:
            np.ndarray: Predictions (0=Clean, 1=Stego)
        """
        if self.model is None:
            raise RuntimeError("Model not initialized or loaded")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """
        Get probability predictions
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            np.ndarray: Probability estimates [[clean_prob, stego_prob], ...]
        """
        if self.model is None:
            raise RuntimeError("Model not initialized or loaded")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_confidence(self, X):
        """
        Get confidence scores (probability of detected class)
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            np.ndarray: Confidence scores (0-1)
        """
        proba = self.predict_proba(X)
        return np.max(proba, axis=1)
    
    def get_feature_importance(self):
        """
        Get feature importance scores
        
        Returns:
            np.ndarray: Importance scores for each feature
        """
        if self.model is None:
            raise RuntimeError("Model not trained")
        
        return self.model.feature_importances_
    
    def cross_validate(self, X, y, cv=5):
        """
        Perform cross-validation
        
        Args:
            X (np.ndarray): Features
            y (np.ndarray): Labels
            cv (int): Number of folds
            
        Returns:
            dict: Cross-validation scores
        """
        X_scaled = self.scaler.fit_transform(X)
        scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='f1')
        return {
            'mean_f1': scores.mean(),
            'std_f1': scores.std(),
            'fold_scores': scores
        }
    
    def save_model(self, path=None):
        """Save trained model and scaler"""
        path = path or self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
    
    def load_model(self, path=None):
        """Load pre-trained model and scaler"""
        path = path or self.model_path
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
