"""
Hybrid Steganalysis System
Combines traditional ML, XGBoost, and deep learning
"""
import json  # Make sure this is imported
import numpy as np
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import tempfile
import atexit
import shutil
import os
import joblib

# ADD THESE IMPORTS TO FIX THE ERROR
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split, cross_val_score

from src.core.ml_classifier import MLSteganalysisClassifier

class HybridSteganalysisSystem:
    """Hybrid steganalysis system combining multiple approaches"""
    
    def __init__(self):
        self.traditional_ensemble = None
        self.xgboost = None
        self.cnn_model = None
        
        self.feature_extractor = None
        self.classifiers = {}
        
        self.load_time = 0
        self.load_path = None
        
        # Track temporary files for cleanup
        self.temp_files = []
        atexit.register(self.cleanup_temp_files)
    
    def cleanup_temp_files(self):
        """Clean up any remaining temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")
    
    def create_ensemble(self):
        """Create traditional ML ensemble"""
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        xgb = self._create_xgboost()
        gbc = GradientBoostingClassifier(n_estimators=100, random_state=42)
        svm = SVC(kernel='rbf', probability=True, random_state=42)
        
        return VotingClassifier(
            estimators=[
                ('rf', rf),
                ('xgb', xgb),
                ('gbc', gbc),
                ('svm', svm)
            ],
            voting='soft',
            n_jobs=-1
        )
    
    def _create_xgboost(self):
        """Create XGBoost classifier with optimal parameters"""
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                gamma=0,
                random_state=42,
                n_jobs=-1
            )
        except ImportError:
            print("XGBoost not available. Install with: pip install xgboost")
            from sklearn.ensemble import GradientBoostingClassifier
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
    
    def train(self, clean_images, stego_images, model_save_path=None, test_size=0.2):
        """Train all components of the hybrid system"""
        # Train traditional ML ensemble
        traditional_metrics = self._train_traditional(clean_images, stego_images, test_size)
        
        # Train XGBoost component
        xgb_metrics = self._train_xgboost(clean_images, stego_images, test_size)
        
        # Train deep learning component (if available)
        cnn_metrics = self._train_cnn(clean_images, stego_images)
        
        # Save model
        if model_save_path:
            self.save_model(model_save_path)
        
        # Return comprehensive metrics
        return self._combine_metrics(traditional_metrics, xgb_metrics, cnn_metrics)
    
    def _train_traditional(self, clean_images, stego_images, test_size):
        """Train traditional ML ensemble"""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        # Use the existing classifier to extract features
        classifier = MLSteganalysisClassifier()
        
        # Train ensemble
        self.traditional_ensemble = self.create_ensemble()
        features, labels = classifier._prepare_training_data(clean_images, stego_images)
        
        # Train ensemble
        self.traditional_ensemble.fit(features, labels)
        
        # Evaluate
        y_pred = self.traditional_ensemble.predict(features)
        return self._calculate_metrics(labels, y_pred)
    
    def _train_xgboost(self, clean_images, stego_images, test_size):
        """Train XGBoost component separately"""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        classifier = MLSteganalysisClassifier()
        features, labels = classifier._prepare_training_data(clean_images, stego_images)
        
        if self.xgboost is None:
            self.xgboost = self._create_xgboost()
        
        # Train XGBoost
        self.xgboost.fit(features, labels)
        
        # Evaluate
        y_pred = self.xgboost.predict(features)
        return self._calculate_metrics(labels, y_pred)
    
    def _train_cnn(self, clean_images, stego_images):
        """Train CNN component (if available)"""
        try:
            from src.core.deep_learning import CNNSteganalysis
            cnn = CNNSteganalysis()
            metrics = cnn.train_model(clean_images, stego_images)
            self.cnn_model = cnn
            return metrics
        except Exception as e:
            print(f"Deep learning training failed: {e}")
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'model_type': 'CNN',
                'error': str(e)
            }
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calculate performance metrics"""
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
            'model_type': 'Ensemble'
        }
    
    def _combine_metrics(self, traditional, xgb, cnn):
        """Combine metrics from all components"""
        return {
            'traditional_ensemble': traditional,
            'xgboost': xgb,
            'cnn': cnn,
            'combined_accuracy': (traditional['accuracy'] + xgb['accuracy']) / 2,
            'overall_confidence': (traditional['f1_score'] + xgb['f1_score']) / 2,
            'training_time': self.load_time,
            'model_path': self.load_path
        }
    
    def predict(self, image_path):
        """Make prediction using the hybrid system"""
        results = {}
        
        # Traditional ensemble prediction
        try:
            from src.core.ml_classifier import MLSteganalysisClassifier
            ml_classifier = MLSteganalysisClassifier()
            
            # Extract features
            features = ml_classifier._extract_features(image_path)
            
            # Convert to feature vector
            feature_vector = ml_classifier.feature_extractor.features_to_vector(features)
            
            # Predict with traditional ensemble
            ensemble_prob = self.traditional_ensemble.predict_proba([feature_vector])[0][1]
            results['traditional'] = {
                'prediction': 1 if ensemble_prob >= 0.5 else 0,
                'probability': ensemble_prob,
                'confidence': self._calculate_confidence(ensemble_prob)
            }
        except Exception as e:
            print(f"Traditional prediction error: {e}")
            results['traditional'] = {'error': str(e)}
        
        # XGBoost prediction
        try:
            xgb_prob = self.xgboost.predict_proba([feature_vector])[0][1]
            results['xgboost'] = {
                'prediction': 1 if xgb_prob >= 0.5 else 0,
                'probability': xgb_prob,
                'confidence': self._calculate_confidence(xgb_prob)
            }
        except Exception as e:
            print(f"XGBoost prediction error: {e}")
            results['xgboost'] = {'error': str(e)}
        
        # CNN prediction
        try:
            if self.cnn_model:
                cnn_prob = self.cnn_model.predict(image_path)
                results['cnn'] = {
                    'prediction': 1 if cnn_prob >= 0.5 else 0,
                    'probability': cnn_prob,
                    'confidence': self._calculate_confidence(cnn_prob)
                }
            else:
                results['cnn'] = {'error': 'Model not available'}
        except Exception as e:
            print(f"CNN prediction error: {e}")
            results['cnn'] = {'error': str(e)}
        
        # Final combined result
        combined_prob = self._combine_predictions(results)
        results['final'] = {
            'prediction': 1 if combined_prob >= 0.5 else 0,
            'probability': combined_prob,
            'confidence': self._calculate_confidence(combined_prob)
        }
        
        return results
    
    def _combine_predictions(self, results):
        """Combine predictions from all models"""
        probabilities = []
        
        # Get probabilities from working models
        for model in ['traditional', 'xgboost', 'cnn']:
            if 'probability' in results.get(model, {}):
                probabilities.append(results[model]['probability'])
        
        # Calculate weighted average
        if probabilities:
            # Weighting: traditional=0.4, xgboost=0.4, cnn=0.2
            weights = [0.4, 0.4, 0.2] if len(probabilities) == 3 else [0.5, 0.5] if len(probabilities) == 2 else [1.0]
            return sum(p * w for p, w in zip(probabilities, weights))
        
        # Fallback to 0.5 if no models worked
        return 0.5
    
    def _calculate_confidence(self, probability):
        """Calculate confidence score (0.0 to 1.0)"""
        return 1.0 - abs(0.5 - probability)
    
    def save_model(self, path):
        """Save all components of the hybrid system"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save traditional ensemble
        ensemble_path = f"{path}_ensemble.pkl"
        joblib.dump(self.traditional_ensemble, ensemble_path)
        
        # Save XGBoost component
        xgb_path = f"{path}_xgb.pkl"
        joblib.dump(self.xgboost, xgb_path)
        
        # Save CNN model (if available)
        if self.cnn_model:
            cnn_path = f"{path}_cnn.h5"
            self.cnn_model.save_model(cnn_path)
        
        # Save metadata
        metadata = {
            'ensemble_path': ensemble_path,
            'xgb_path': xgb_path,
            'cnn_path': cnn_path if self.cnn_model else None,
            'creation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        metadata_path = f"{path}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.load_path = path
        return path
    
    def load_model(self, path):
        """Load all components of the hybrid system"""
        try:
            # Load metadata
            metadata_path = f"{path}_metadata.json"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Load traditional ensemble
            if os.path.exists(metadata['ensemble_path']):
                self.traditional_ensemble = joblib.load(metadata['ensemble_path'])
            
            # Load XGBoost component
            if os.path.exists(metadata['xgb_path']):
                self.xgboost = joblib.load(metadata['xgb_path'])
            
            # Load CNN model
            if metadata['cnn_path'] and os.path.exists(metadata['cnn_path']):
                from src.core.deep_learning import CNNSteganalysis
                self.cnn_model = CNNSteganalysis()
                self.cnn_model.load_model(metadata['cnn_path'])
            
            self.load_path = path
            return True
            
        except Exception as e:
            print(f"Error loading hybrid model: {e}")
            return False