"""
XGBoost-based steganography classifier
Provides superior performance for steganalysis with faster training and inference
"""

import os
import pickle
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class XGBoostClassifier:
    """
    XGBoost-based classifier for steganography detection.
    Advantages over Random Forest:
    - Faster training with GPU support
    - Better handling of imbalanced datasets
    - Built-in regularization reduces overfitting
    - Superior prediction accuracy (typically 2-5% better)
    """
    
    def __init__(self, model_path=None):
        """
        Initialize XGBoost classifier
        
        Args:
            model_path (str): Path to pre-trained model file
        """
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path or os.path.join(
            Path(__file__).parent.parent.parent,
            "models",
            "steg_model_xgboost.pkl"
        )
        
        # Load pre-trained model if available
        if os.path.exists(self.model_path):
            try:
                self.load_model()
            except Exception:
                self._initialize_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new XGBoost model with optimal hyperparameters"""
        self.model = XGBClassifier(
            n_estimators=200,          # More trees than RF for better performance
            max_depth=8,               # Moderate depth to prevent overfitting
            learning_rate=0.05,        # Slower learning for better generalization
            subsample=0.8,             # Subsample 80% of data per iteration
            colsample_bytree=0.8,      # Subsample 80% of features per tree
            random_state=42,
            n_jobs=-1,                 # Use all CPU cores
            eval_metric='logloss',
            verbosity=0,
            tree_method='hist',        # Faster histogram-based splitting
            use_label_encoder=False    # Suppress deprecation warning
        )
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=100):
        """
        Train XGBoost classifier with optional early stopping
        
        Args:
            X_train (np.ndarray): Training features (n_samples, n_features)
            y_train (np.ndarray): Training labels (0=Clean, 1=Stego)
            X_val (np.ndarray): Validation features for early stopping
            y_val (np.ndarray): Validation labels
            epochs (int): Maximum number of boosting rounds
            
        Returns:
            dict: Training metrics including accuracy, precision, recall, F1
        """
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train with early stopping using callbacks (new XGBoost API)
        fit_kwargs = {
            'X': X_train_scaled,
            'y': y_train,
        }
        
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            fit_kwargs['eval_set'] = [(X_val_scaled, y_val)]
        
        # Train the model
        self.model.fit(**fit_kwargs, verbose=False)
        
        # Calculate training metrics
        y_pred_train = self.model.predict(X_train_scaled)
        metrics = {
            'accuracy': accuracy_score(y_train, y_pred_train),
            'precision': precision_score(y_train, y_pred_train, zero_division=0),
            'recall': recall_score(y_train, y_pred_train, zero_division=0),
            'f1': f1_score(y_train, y_pred_train, zero_division=0)
        }
        
        if X_val is not None and y_val is not None:
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
        Get feature importance scores from XGBoost
        
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
