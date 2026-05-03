"""
Machine Learning Classifier for Steganography Detection
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import os
from pathlib import Path
from typing import Dict, List, Tuple
import json
from .ml_features import MLFeatureExtractor

class MLSteganalysisClassifier:
    """Machine Learning-based steganography detection"""
    
    def __init__(self, model_path=None):
        self.model = None
        self.scaler = None
        self.feature_extractor = MLFeatureExtractor()
        self.model_path = model_path
        self.feature_names = []
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def train_model(self, clean_images: List[str], stego_images: List[str], 
                   model_save_path: str = None, test_size: float = 0.2) -> Dict:
        """
        Train the ML classifier
        Returns training metrics
        """
        print("Extracting features from clean images...")
        clean_features = []
        for img_path in clean_images:
            features = self.feature_extractor.extract_features(img_path)
            if features:
                clean_features.append(features)
        
        print("Extracting features from stego images...")
        stego_features = []
        for img_path in stego_images:
            features = self.feature_extractor.extract_features(img_path)
            if features:
                stego_features.append(features)
        
        if not clean_features or not stego_features:
            raise ValueError("No features extracted from images")
        
        # Prepare training data
        X_clean = [self.feature_extractor.features_to_vector(f) for f in clean_features]
        X_stego = [self.feature_extractor.features_to_vector(f) for f in stego_features]
        
        X = np.array(X_clean + X_stego)
        y = np.array([0] * len(X_clean) + [1] * len(X_stego))
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train Random Forest
        print("Training Random Forest classifier...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        metrics = self._calculate_metrics(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5)
        metrics['cv_mean'] = float(np.mean(cv_scores))
        metrics['cv_std'] = float(np.std(cv_scores))
        
        # Feature importance
        self.feature_names = self.feature_extractor.get_feature_names()
        metrics['feature_importance'] = dict(zip(
            self.feature_names, 
            self.model.feature_importances_
        ))
        
        # Save model
        if model_save_path:
            self.save_model(model_save_path)
        
        return metrics
    
    def predict(self, image_path: str) -> Dict:
        """
        Predict if image contains steganography
        Returns prediction dictionary with probability and confidence
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Extract features
        features = self.feature_extractor.extract_features(image_path)
        if not features:
            return {
                'prediction': -1,
                'probability': 0.0,
                'confidence': 0.0,
                'error': 'Failed to extract features'
            }
        
        # Convert to vector
        feature_vector = np.array([self.feature_extractor.features_to_vector(features)])
        
        # Scale features
        if self.scaler:
            feature_vector = self.scaler.transform(feature_vector)
        
        # Predict
        prediction = self.model.predict(feature_vector)[0]
        probability = self.model.predict_proba(feature_vector)[0]
        
        # Calculate confidence (max probability)
        confidence = float(max(probability))
        
        return {
            'prediction': int(prediction),  # 0 = clean, 1 = stego
            'probability': float(probability[1]),  # Probability of stego
            'confidence': confidence,
            'error': None
        }
    
    def _prepare_training_data(self, clean_images: List[str], stego_images: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data by extracting features from images
        
        Args:
            clean_images: List of paths to clean images
            stego_images: List of paths to stego images
            
        Returns:
            X: Feature matrix
            y: Label vector (0 for clean, 1 for stego)
        """
        print("Preparing training data...")
        
        # Extract features from clean images
        clean_features = []
        for img_path in clean_images:
            features = self.feature_extractor.extract_features(img_path)
            if features:
                clean_features.append(features)
        
        # Extract features from stego images
        stego_features = []
        for img_path in stego_images:
            features = self.feature_extractor.extract_features(img_path)
            if features:
                stego_features.append(features)
        
        # Convert to feature vectors
        X_clean = [self.feature_extractor.features_to_vector(f) for f in clean_features]
        X_stego = [self.feature_extractor.features_to_vector(f) for f in stego_features]
        
        # Create feature matrix and labels
        X = np.array(X_clean + X_stego)
        y = np.array([0] * len(X_clean) + [1] * len(X_stego))
        
        return X, y
    
    def _calculate_metrics(self, y_true, y_pred) -> Dict:
        """Calculate classification metrics"""
        metrics = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred)),
            'recall': float(recall_score(y_true, y_pred)),
            'f1_score': float(f1_score(y_true, y_pred)),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }
        return metrics
    
    def save_model(self, model_path: str):
        """Save trained model and scaler"""
        model_dir = Path(model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_extractor': self.feature_extractor
        }
        
        joblib.dump(model_data, model_path)
        print(f"Model saved to {model_path}")
    
    def load_model(self, model_path: str):
        """Load trained model and scaler"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        model_data = joblib.load(model_path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        
        # Handle old models that don't have feature_names
        if 'feature_names' in model_data:
            self.feature_names = model_data['feature_names']
        else:
            self.feature_names = self.feature_extractor.get_feature_names()
        
        # Handle old models that don't have feature_extractor
        if 'feature_extractor' in model_data:
            self.feature_extractor = model_data['feature_extractor']
        else:
            # Create a new feature extractor (will work but may have different feature order)
            self.feature_extractor = MLFeatureExtractor()
        
        self.model_path = model_path
        print(f"Model loaded from {model_path}")
    
    def evaluate_model(self, test_images: List[str], true_labels: List[int]) -> Dict:
        """
        Evaluate model on test set
        Returns metrics and individual predictions
        """
        predictions = []
        probabilities = []
        
        for img_path in test_images:
            result = self.predict(img_path)
            predictions.append(result['prediction'])
            probabilities.append(result['probability'])
        
        metrics = self._calculate_metrics(true_labels, predictions)
        metrics['predictions'] = predictions
        metrics['probabilities'] = probabilities
        
        return metrics
