"""
Comprehensive tests for XGBoost, SVM, and Ensemble ML models
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

# Test imports
from src.core.ml_rf_classifier import RandomForestClassifier
from src.core.ml_xgboost_classifier import XGBoostClassifier
from src.core.ml_svm_classifier import SVMClassifier
from src.core.ml_ensemble_classifier import EnsembleMLClassifier, VotingStrategy
from src.core.ml_multi_model_manager import MultiModelMLManager
from src.core.ml_features import MLFeatureExtractor


class TestXGBoostClassifier:
    """Tests for XGBoost classifier"""
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic training data"""
        np.random.seed(42)
        X_train = np.random.randn(100, 48)  # 48 features
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.randn(20, 48)
        y_val = np.random.randint(0, 2, 20)
        return X_train, y_train, X_val, y_val
    
    def test_xgboost_initialization(self):
        """Test XGBoost classifier initialization"""
        clf = XGBoostClassifier()
        assert clf.model is not None
        assert clf.scaler is not None
    
    def test_xgboost_training(self, synthetic_data):
        """Test XGBoost model training"""
        X_train, y_train, X_val, y_val = synthetic_data
        clf = XGBoostClassifier()
        
        metrics = clf.train(X_train, y_train, X_val, y_val)
        
        assert 'accuracy' in metrics
        assert 'f1' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['f1'] <= 1
    
    def test_xgboost_prediction(self, synthetic_data):
        """Test XGBoost predictions"""
        X_train, y_train, _, _ = synthetic_data
        clf = XGBoostClassifier()
        clf.train(X_train, y_train)
        
        predictions = clf.predict(X_train[:5])
        assert len(predictions) == 5
        assert all(p in [0, 1] for p in predictions)
    
    def test_xgboost_proba(self, synthetic_data):
        """Test probability predictions"""
        X_train, y_train, _, _ = synthetic_data
        clf = XGBoostClassifier()
        clf.train(X_train, y_train)
        
        proba = clf.predict_proba(X_train[:5])
        assert proba.shape == (5, 2)
        assert np.all((proba >= 0) & (proba <= 1))
        assert np.allclose(proba.sum(axis=1), 1.0)
    
    def test_xgboost_confidence(self, synthetic_data):
        """Test confidence scores"""
        X_train, y_train, _, _ = synthetic_data
        clf = XGBoostClassifier()
        clf.train(X_train, y_train)
        
        confidences = clf.get_confidence(X_train[:5])
        assert len(confidences) == 5
        assert np.all((confidences >= 0) & (confidences <= 1))
    
    def test_xgboost_feature_importance(self, synthetic_data):
        """Test feature importance extraction"""
        X_train, y_train, _, _ = synthetic_data
        clf = XGBoostClassifier()
        clf.train(X_train, y_train)
        
        importance = clf.get_feature_importance()
        assert len(importance) == 48
        assert np.all(importance >= 0)
    
    def test_xgboost_save_load(self, synthetic_data):
        """Test model saving and loading"""
        X_train, y_train, _, _ = synthetic_data
        clf1 = XGBoostClassifier()
        clf1.train(X_train, y_train)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_xgboost.pkl')
            clf1.save_model(model_path)
            
            clf2 = XGBoostClassifier(model_path=model_path)
            
            pred1 = clf1.predict(X_train[:5])
            pred2 = clf2.predict(X_train[:5])
            
            assert np.array_equal(pred1, pred2)


class TestSVMClassifier:
    """Tests for SVM classifier"""
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic training data"""
        np.random.seed(42)
        X_train = np.random.randn(100, 48)
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.randn(20, 48)
        y_val = np.random.randint(0, 2, 20)
        return X_train, y_train, X_val, y_val
    
    def test_svm_initialization(self):
        """Test SVM classifier initialization"""
        clf = SVMClassifier()
        assert clf.model is not None
        assert clf.scaler is not None
        assert clf.kernel == 'rbf'
    
    def test_svm_training(self, synthetic_data):
        """Test SVM model training"""
        X_train, y_train, X_val, y_val = synthetic_data
        clf = SVMClassifier()
        
        metrics = clf.train(X_train, y_train, X_val, y_val)
        
        assert 'accuracy' in metrics
        assert 'f1' in metrics
        assert 0 <= metrics['accuracy'] <= 1
    
    def test_svm_prediction(self, synthetic_data):
        """Test SVM predictions"""
        X_train, y_train, _, _ = synthetic_data
        clf = SVMClassifier()
        clf.train(X_train, y_train)
        
        predictions = clf.predict(X_train[:5])
        assert len(predictions) == 5
        assert all(p in [0, 1] for p in predictions)
    
    def test_svm_proba(self, synthetic_data):
        """Test SVM probability predictions"""
        X_train, y_train, _, _ = synthetic_data
        clf = SVMClassifier()
        clf.train(X_train, y_train)
        
        proba = clf.predict_proba(X_train[:5])
        assert proba.shape == (5, 2)
        assert np.allclose(proba.sum(axis=1), 1.0)
    
    def test_svm_support_vectors(self, synthetic_data):
        """Test support vector access"""
        X_train, y_train, _, _ = synthetic_data
        clf = SVMClassifier()
        clf.train(X_train, y_train)
        
        n_support = clf.get_n_support_vectors()
        assert len(n_support) == 2  # One for each class
    
    def test_svm_cross_validation(self, synthetic_data):
        """Test cross-validation"""
        X_train, y_train, _, _ = synthetic_data
        clf = SVMClassifier()
        clf.train(X_train, y_train)
        
        cv_results = clf.cross_validate(X_train, y_train, cv=3)
        assert 'mean_f1' in cv_results
        assert 'fold_scores' in cv_results
        assert len(cv_results['fold_scores']) == 3


class TestEnsembleClassifier:
    """Tests for Ensemble classifier"""
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic training data"""
        np.random.seed(42)
        X_train = np.random.randn(100, 48)
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.randn(20, 48)
        y_val = np.random.randint(0, 2, 20)
        return X_train, y_train, X_val, y_val
    
    def test_ensemble_initialization(self):
        """Test ensemble classifier initialization"""
        clf = EnsembleMLClassifier()
        assert clf.scaler is not None
        assert clf.weights == [0.3, 0.4, 0.3]
        # Model is created during training, not at initialization
    
    def test_ensemble_training(self, synthetic_data):
        """Test ensemble model training"""
        X_train, y_train, X_val, y_val = synthetic_data
        clf = EnsembleMLClassifier()
        
        metrics = clf.train(X_train, y_train, X_val, y_val)
        
        assert 'accuracy' in metrics
        assert 'f1' in metrics
        assert 'rf_f1' in metrics
        assert 'xgb_f1' in metrics
        assert 'svm_f1' in metrics
    
    def test_ensemble_prediction(self, synthetic_data):
        """Test ensemble predictions"""
        X_train, y_train, _, _ = synthetic_data
        clf = EnsembleMLClassifier()
        clf.train(X_train, y_train)
        
        predictions = clf.predict(X_train[:5])
        assert len(predictions) == 5
        assert all(p in [0, 1] for p in predictions)
    
    def test_ensemble_individual_predictions(self, synthetic_data):
        """Test getting individual model predictions"""
        X_train, y_train, _, _ = synthetic_data
        clf = EnsembleMLClassifier()
        clf.train(X_train, y_train)
        
        individual_preds = clf.get_individual_predictions(X_train[:5])
        
        assert 'rf_pred' in individual_preds
        assert 'xgb_pred' in individual_preds
        assert 'svm_pred' in individual_preds
    
    def test_ensemble_weight_adjustment(self, synthetic_data):
        """Test weight adjustment"""
        X_train, y_train, _, _ = synthetic_data
        clf = EnsembleMLClassifier()
        clf.train(X_train, y_train)
        
        new_weights = [0.2, 0.5, 0.3]
        clf.set_model_weights(new_weights)
        assert np.allclose(clf.weights, new_weights)


class TestMultiModelManager:
    """Tests for MultiModelMLManager"""
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic training data"""
        np.random.seed(42)
        X_train = np.random.randn(100, 48)
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.randn(20, 48)
        y_val = np.random.randint(0, 2, 20)
        return X_train, y_train, X_val, y_val
    
    def test_manager_initialization(self):
        """Test MultiModelMLManager initialization"""
        manager = MultiModelMLManager()
        assert manager.current_model is not None
        assert len(manager.get_available_models()) > 0
    
    def test_manager_model_switching(self):
        """Test switching between models"""
        manager = MultiModelMLManager(model_type='ensemble')
        available = manager.get_available_models()
        
        if 'xgb' in available:
            manager.set_model('xgb')
            assert manager.model_type == 'xgb'
    
    def test_manager_predict_with_confidence(self, synthetic_data):
        """Test predictions with confidence"""
        X_train, y_train, _, _ = synthetic_data
        
        manager = MultiModelMLManager()
        # Train all models
        manager.train_all_models(X_train, y_train)
        
        results = manager.predict_with_confidence(X_train[:5])
        
        assert 'predictions' in results
        assert 'confidences' in results
        assert 'model' in results
    
    def test_manager_predict_all_models(self, synthetic_data):
        """Test predictions from all models"""
        X_train, y_train, _, _ = synthetic_data
        
        manager = MultiModelMLManager()
        manager.train_all_models(X_train, y_train)
        
        all_results = manager.predict_all_models(X_train[:5])
        
        assert len(all_results) > 0
        for model_name, result in all_results.items():
            if 'error' not in result:
                assert 'predictions' in result
                assert 'confidences' in result
    
    def test_manager_compare_models(self, synthetic_data):
        """Test model comparison"""
        X_train, y_train, X_val, y_val = synthetic_data
        
        manager = MultiModelMLManager()
        manager.train_all_models(X_train, y_train)
        
        comparison = manager.compare_models(X_val, y_val)
        
        assert len(comparison) > 0
        for model_name, metrics in comparison.items():
            if 'error' not in metrics:
                assert 'mean_confidence' in metrics
                assert 'accuracy' in metrics


class TestVotingStrategy:
    """Tests for voting strategies"""
    
    def test_hard_voting(self):
        """Test hard voting"""
        predictions = {
            'rf_pred': 1,
            'xgb_pred': 1,
            'svm_pred': 0
        }
        
        result = VotingStrategy.hard_voting(predictions)
        assert result == 1  # Majority vote
    
    def test_weighted_voting(self):
        """Test weighted voting"""
        predictions = {'rf_pred': 1, 'xgb_pred': 0, 'svm_pred': 0}
        confidences = {'rf_confidence': 0.9, 'xgb_confidence': 0.6, 'svm_confidence': 0.7}
        
        result = VotingStrategy.weighted_voting(predictions, confidences)
        assert result in [0, 1]


class TestRealImageAnalysis:
    """Tests with real image features (integration tests)"""
    
    @pytest.fixture
    def sample_image(self, conftest_tmpdir=None):
        """Create a sample test image"""
        from PIL import Image
        
        if conftest_tmpdir is None:
            tmpdir = tempfile.mkdtemp()
        else:
            tmpdir = conftest_tmpdir
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_path = os.path.join(tmpdir, 'test_image.png')
        img.save(img_path)
        
        return img_path
    
    def test_feature_extraction_consistency(self, sample_image):
        """Test that feature extraction is consistent"""
        extractor = MLFeatureExtractor()
        
        features1_dict = extractor.extract_features(sample_image)
        features2_dict = extractor.extract_features(sample_image)
        
        # Convert dict to vector
        features1 = extractor.features_to_vector(features1_dict) if isinstance(features1_dict, dict) else features1_dict
        features2 = extractor.features_to_vector(features2_dict) if isinstance(features2_dict, dict) else features2_dict
        
        assert np.allclose(features1, features2)
        assert len(features1) == 48
        assert not np.any(np.isnan(features1))
    
    def test_xgboost_with_real_features(self, sample_image):
        """Test XGBoost with real extracted features"""
        extractor = MLFeatureExtractor()
        features_dict = extractor.extract_features(sample_image)
        features = extractor.features_to_vector(features_dict) if isinstance(features_dict, dict) else features_dict
        
        clf = XGBoostClassifier()
        
        # Create synthetic training data
        X_train = np.vstack([features] * 50)
        y_train = np.hstack([0] * 25 + [1] * 25)
        
        metrics = clf.train(X_train, y_train)
        assert metrics['f1'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
