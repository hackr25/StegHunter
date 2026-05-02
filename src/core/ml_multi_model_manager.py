"""
Multi-Model ML Manager for StegHunter
Unified interface to access Random Forest, XGBoost, SVM, and Ensemble models
"""

import os
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from src.core.ml_rf_classifier import RandomForestClassifier
from src.core.ml_xgboost_classifier import XGBoostClassifier
from src.core.ml_svm_classifier import SVMClassifier
from src.core.ml_ensemble_classifier import EnsembleMLClassifier
from src.core.ml_features import MLFeatureExtractor
from src.core.temporal_feature_extractor import TemporalFeatureExtractor


class MultiModelMLManager:
    """
    Manages multiple ML models with unified interface.
    Allows easy switching between different classifiers and ensemble voting.
    """
    
    def __init__(self, model_type='ensemble'):
        """
        Initialize multi-model manager
        
        Args:
            model_type (str): 'rf' (Random Forest), 'xgb' (XGBoost), 
                             'svm' (SVM), 'ensemble' (default)
        """
        self.model_type = model_type
        self.current_model = None
        self.models = {
            'rf': None,
            'xgb': None,
            'svm': None,
            'ensemble': None
        }
        self._load_or_initialize_models()
    
    def _load_or_initialize_models(self):
        """Load pre-trained models or initialize new ones"""
        print("Loading ML models...")
        
        try:
            self.models['rf'] = RandomForestClassifier()
            print("  ✅ Random Forest loaded")
        except Exception as e:
            print(f"  ⚠️  Random Forest failed: {e}")
        
        try:
            self.models['xgb'] = XGBoostClassifier()
            print("  ✅ XGBoost loaded")
        except Exception as e:
            print(f"  ⚠️  XGBoost failed: {e}")
        
        try:
            self.models['svm'] = SVMClassifier()
            print("  ✅ SVM loaded")
        except Exception as e:
            print(f"  ⚠️  SVM failed: {e}")
        
        try:
            self.models['ensemble'] = EnsembleMLClassifier()
            print("  ✅ Ensemble loaded")
        except Exception as e:
            print(f"  ⚠️  Ensemble failed: {e}")
        
        # Set current model
        if self.models[self.model_type] is not None:
            self.current_model = self.models[self.model_type]
        else:
            # Fallback to first available model
            for model_type in ['ensemble', 'xgb', 'rf', 'svm']:
                if self.models[model_type] is not None:
                    self.current_model = self.models[model_type]
                    self.model_type = model_type
                    break
    
    def set_model(self, model_type):
        """
        Switch to a different model
        
        Args:
            model_type (str): 'rf', 'xgb', 'svm', or 'ensemble'
        """
        if model_type not in self.models:
            raise ValueError(f"Unknown model type: {model_type}. Must be 'rf', 'xgb', 'svm', or 'ensemble'")
        
        if self.models[model_type] is None:
            raise RuntimeError(f"{model_type} model not available")
        
        self.current_model = self.models[model_type]
        self.model_type = model_type
        print(f"Switched to {model_type.upper()} model")
    
    def predict(self, X, model_type=None):
        """
        Make predictions with specified or current model
        
        Args:
            X (np.ndarray): Features array
            model_type (str): Optional model override
            
        Returns:
            np.ndarray: Predictions (0=Clean, 1=Stego)
        """
        if model_type:
            self.set_model(model_type)
        
        return self.current_model.predict(X)
    
    def predict_with_confidence(self, X, model_type=None):
        """
        Get predictions with confidence scores
        
        Args:
            X (np.ndarray): Features array
            model_type (str): Optional model override
            
        Returns:
            dict: Predictions and confidences
        """
        if model_type:
            self.set_model(model_type)
        
        predictions = self.current_model.predict(X)
        confidences = self.current_model.get_confidence(X)
        
        return {
            'predictions': predictions,
            'confidences': confidences,
            'model': self.model_type
        }
    
    def predict_all_models(self, X):
        """
        Get predictions from all available models
        
        Args:
            X (np.ndarray): Features array
            
        Returns:
            dict: Predictions from each model with confidence
        """
        results = {}
        
        for model_name in ['rf', 'xgb', 'svm', 'ensemble']:
            if self.models[model_name] is not None:
                try:
                    pred = self.models[model_name].predict(X)
                    conf = self.models[model_name].get_confidence(X)
                    
                    results[model_name] = {
                        'predictions': pred,
                        'confidences': conf,
                        'mean_confidence': conf.mean() if len(conf) > 0 else 0.0
                    }
                except Exception as e:
                    results[model_name] = {'error': str(e)}
        
        return results
    
    def compare_models(self, X, y_true=None):
        """
        Compare predictions across all models
        
        Args:
            X (np.ndarray): Features
            y_true (np.ndarray): True labels for comparison
            
        Returns:
            dict: Comparison metrics for each model
        """
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
        
        comparison = {}
        predictions_all = self.predict_all_models(X)
        
        for model_name, results in predictions_all.items():
            if 'error' in results:
                comparison[model_name] = {'status': 'error', 'message': results['error']}
            else:
                metrics = {
                    'mean_confidence': results['mean_confidence'],
                    'min_confidence': results['confidences'].min(),
                    'max_confidence': results['confidences'].max()
                }
                
                if y_true is not None:
                    preds = results['predictions']
                    metrics['accuracy'] = accuracy_score(y_true, preds)
                    metrics['f1'] = f1_score(y_true, preds, zero_division=0)
                    metrics['precision'] = precision_score(y_true, preds, zero_division=0)
                    metrics['recall'] = recall_score(y_true, preds, zero_division=0)
                
                comparison[model_name] = metrics
        
        return comparison
    
    def train_all_models(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train all available models
        
        Args:
            X_train (np.ndarray): Training features
            y_train (np.ndarray): Training labels
            X_val (np.ndarray): Validation features
            y_val (np.ndarray): Validation labels
            
        Returns:
            dict: Training metrics for each model
        """
        training_results = {}
        
        print("\n" + "="*60)
        print("TRAINING ALL MODELS")
        print("="*60 + "\n")
        
        if self.models['rf'] is not None:
            print("Training Random Forest...")
            try:
                training_results['rf'] = self.models['rf'].train(X_train, y_train, X_val, y_val)
                self.models['rf'].save_model()
                print(f"  ✅ F1: {training_results['rf']['f1']:.4f}\n")
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
        
        if self.models['xgb'] is not None:
            print("Training XGBoost...")
            try:
                training_results['xgb'] = self.models['xgb'].train(X_train, y_train, X_val, y_val)
                self.models['xgb'].save_model()
                print(f"  ✅ F1: {training_results['xgb']['f1']:.4f}\n")
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
        
        if self.models['svm'] is not None:
            print("Training SVM...")
            try:
                training_results['svm'] = self.models['svm'].train(X_train, y_train, X_val, y_val)
                self.models['svm'].save_model()
                print(f"  ✅ F1: {training_results['svm']['f1']:.4f}\n")
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
        
        if self.models['ensemble'] is not None:
            print("Training Ensemble (RF + XGB + SVM)...")
            try:
                training_results['ensemble'] = self.models['ensemble'].train(X_train, y_train, X_val, y_val)
                self.models['ensemble'].save_model()
                print(f"  ✅ F1: {training_results['ensemble']['f1']:.4f}\n")
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
        
        return training_results
    
    def get_available_models(self):
        """Get list of available models"""
        return [name for name, model in self.models.items() if model is not None]
    
    def get_best_model(self, X, y_true):
        """
        Determine which model performs best on given data
        
        Args:
            X (np.ndarray): Features
            y_true (np.ndarray): True labels
            
        Returns:
            dict: Best model info
        """
        from sklearn.metrics import f1_score
        
        comparison = self.compare_models(X, y_true)
        
        best_model = None
        best_f1 = -1
        
        for model_name, metrics in comparison.items():
            if 'f1' in metrics and metrics['f1'] > best_f1:
                best_f1 = metrics['f1']
                best_model = model_name
        
        return {
            'model': best_model,
            'f1': best_f1,
            'all_results': comparison
        }
    
    def train_all_models_with_video(self, clean_image_dir: str, stego_image_dir: str,
                                    clean_video_dir: Optional[str] = None,
                                    stego_video_dir: Optional[str] = None,
                                    include_temporal_features: bool = True) -> Dict:
        """
        Train all models with combined image + video data
        
        Args:
            clean_image_dir: Directory with clean images
            stego_image_dir: Directory with stego images
            clean_video_dir: Directory with clean videos (optional)
            stego_video_dir: Directory with stego videos (optional)
            include_temporal_features: Include temporal features from videos
            
        Returns:
            dict: Training results for all models
        """
        print("\n" + "="*60)
        print("EXTRACTING TRAINING FEATURES (IMAGES + VIDEOS)")
        print("="*60)
        
        feature_extractor = MLFeatureExtractor()
        temporal_extractor = TemporalFeatureExtractor()
        
        # Extract image features
        print("\n📸 Extracting image features...")
        X_clean_img = []
        X_stego_img = []
        
        clean_images = list(Path(clean_image_dir).rglob('*'))
        stego_images = list(Path(stego_image_dir).rglob('*'))
        
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        for img_path in clean_images:
            if img_path.suffix.lower() in supported_formats:
                try:
                    features = feature_extractor.extract_features(str(img_path))
                    if features:
                        feat_vec = feature_extractor.features_to_vector(features)
                        X_clean_img.append(feat_vec)
                except Exception as e:
                    print(f"  ⚠️ Error processing {img_path}: {e}")
        
        for img_path in stego_images:
            if img_path.suffix.lower() in supported_formats:
                try:
                    features = feature_extractor.extract_features(str(img_path))
                    if features:
                        feat_vec = feature_extractor.features_to_vector(features)
                        X_stego_img.append(feat_vec)
                except Exception as e:
                    print(f"  ⚠️ Error processing {img_path}: {e}")
        
        print(f"  ✓ Extracted {len(X_clean_img)} clean image features")
        print(f"  ✓ Extracted {len(X_stego_img)} stego image features")
        
        # Extract video features if provided
        X_clean_vid = []
        X_stego_vid = []
        
        if clean_video_dir and os.path.exists(clean_video_dir):
            print("\n🎬 Extracting video features (clean)...")
            clean_videos = list(Path(clean_video_dir).rglob('*'))
            supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
            
            for vid_path in clean_videos:
                if vid_path.suffix.lower() in supported_video_formats:
                    try:
                        temporal_features = temporal_extractor.extract_video_temporal_features(
                            str(vid_path), num_batches=5
                        )
                        if temporal_features:
                            # Convert features dict to vector
                            feat_vec = np.array(list(temporal_features.values()))
                            X_clean_vid.append(feat_vec)
                            print(f"  ✓ {vid_path.name}")
                    except Exception as e:
                        print(f"  ⚠️ Error processing {vid_path}: {e}")
        
        if stego_video_dir and os.path.exists(stego_video_dir):
            print("\n🎬 Extracting video features (stego)...")
            stego_videos = list(Path(stego_video_dir).rglob('*'))
            
            for vid_path in stego_videos:
                if vid_path.suffix.lower() in supported_video_formats:
                    try:
                        temporal_features = temporal_extractor.extract_video_temporal_features(
                            str(vid_path), num_batches=5
                        )
                        if temporal_features:
                            feat_vec = np.array(list(temporal_features.values()))
                            X_stego_vid.append(feat_vec)
                            print(f"  ✓ {vid_path.name}")
                    except Exception as e:
                        print(f"  ⚠️ Error processing {vid_path}: {e}")
        
        print(f"  ✓ Extracted {len(X_clean_vid)} clean video features")
        print(f"  ✓ Extracted {len(X_stego_vid)} stego video features")
        
        # Combine image and video features
        print("\n🔗 Combining image and video features...")
        
        # Pad video features to match image feature dimension if needed
        if X_clean_vid and X_clean_img:
            img_dim = len(X_clean_img[0])
            vid_dim = len(X_clean_vid[0])
            
            if vid_dim < img_dim:
                # Pad video features
                X_clean_vid_padded = [np.pad(v, (0, img_dim - vid_dim)) for v in X_clean_vid]
                X_stego_vid_padded = [np.pad(v, (0, img_dim - vid_dim)) for v in X_stego_vid]
            else:
                X_clean_vid_padded = X_clean_vid
                X_stego_vid_padded = X_stego_vid
            
            X_clean = np.array(X_clean_img + X_clean_vid_padded)
            X_stego = np.array(X_stego_img + X_stego_vid_padded)
        else:
            X_clean = np.array(X_clean_img)
            X_stego = np.array(X_stego_img)
        
        X_train = np.vstack([X_clean, X_stego])
        y_train = np.array([0] * len(X_clean) + [1] * len(X_stego))
        
        print(f"  ✓ Total training samples: {len(X_train)}")
        print(f"  ✓ Feature dimension: {X_train.shape[1]}")
        
        # Train all models with combined data
        return self.train_all_models(X_train, y_train)

