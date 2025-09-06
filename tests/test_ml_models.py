"""
Unit tests for ML models functionality
"""
import pytest
import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ml_models import EngineHealthPredictor, generate_training_data

class TestEngineHealthPredictor:
    def setup_method(self):
        """Setup test fixtures"""
        self.predictor = EngineHealthPredictor()
        self.sample_data = generate_training_data(num_engines=5, cycles_per_engine=50)
    
    def test_model_initialization(self):
        """Test model initialization"""
        assert self.predictor.rul_model is None
        assert self.predictor.anomaly_model is None
        assert self.predictor.scaler is None
        assert self.predictor.feature_columns is None
    
    def test_training_data_generation(self):
        """Test training data generation"""
        data = generate_training_data(num_engines=3, cycles_per_engine=10)
        
        # Check basic structure
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 30  # 3 engines * 10 cycles
        assert 'engine_id' in data.columns
        assert 'cycle' in data.columns
        assert 'rul' in data.columns
        
        # Check sensor columns
        sensor_columns = [col for col in data.columns if col.startswith('sensor_')]
        assert len(sensor_columns) == 21  # NASA C-MAPSS sensors
    
    def test_rul_model_training(self):
        """Test RUL model training"""
        success = self.predictor.train_rul_model(self.sample_data)
        
        assert success is True
        assert self.predictor.rul_model is not None
        assert self.predictor.scaler is not None
        assert self.predictor.feature_columns is not None
    
    def test_anomaly_model_training(self):
        """Test anomaly detection model training"""
        # First train RUL model (required for feature columns)
        self.predictor.train_rul_model(self.sample_data)
        
        success = self.predictor.train_anomaly_model(self.sample_data)
        
        assert success is True
        assert self.predictor.anomaly_model is not None
    
    def test_rul_prediction(self):
        """Test RUL prediction functionality"""
        # Train model first
        self.predictor.train_rul_model(self.sample_data)
        
        # Test prediction
        test_data = self.sample_data.head(5)
        predictions = self.predictor.predict_rul(test_data)
        
        assert len(predictions) == 5
        assert all(isinstance(pred, (int, float)) for pred in predictions)
        assert all(pred >= 0 for pred in predictions)  # RUL should be non-negative
    
    def test_anomaly_detection(self):
        """Test anomaly detection functionality"""
        # Train models first
        self.predictor.train_rul_model(self.sample_data)
        self.predictor.train_anomaly_model(self.sample_data)
        
        # Test anomaly detection
        test_data = self.sample_data.head(10)
        scores, predictions = self.predictor.detect_anomalies(test_data)
        
        assert len(scores) == 10
        assert len(predictions) == 10
        assert all(isinstance(score, (int, float)) for score in scores)
        assert all(pred in [-1, 1] for pred in predictions)  # Isolation Forest outputs
    
    def test_early_warning_system(self):
        """Test early warning system"""
        # Train models first
        self.predictor.train_rul_model(self.sample_data)
        self.predictor.train_anomaly_model(self.sample_data)
        
        # Test early warning
        warnings = self.predictor.early_warning_system(self.sample_data.tail(20))
        
        assert isinstance(warnings, list)
        for warning in warnings:
            assert 'engine_id' in warning
            assert 'predicted_rul' in warning
            assert 'warning_level' in warning
            assert warning['warning_level'] in ['GREEN', 'YELLOW', 'RED']
    
    def test_model_persistence(self):
        """Test model saving and loading"""
        # Train models
        self.predictor.train_rul_model(self.sample_data)
        self.predictor.train_anomaly_model(self.sample_data)
        
        # Save models
        self.predictor.save_models()
        
        # Check files exist
        assert os.path.exists('/Users/raksharane/Documents/ruku/aircraft-engine-monitoring/models/rul_model.pkl')
        assert os.path.exists('/Users/raksharane/Documents/ruku/aircraft-engine-monitoring/models/anomaly_model.pkl')
        assert os.path.exists('/Users/raksharane/Documents/ruku/aircraft-engine-monitoring/models/scaler.pkl')
        assert os.path.exists('/Users/raksharane/Documents/ruku/aircraft-engine-monitoring/models/feature_columns.pkl')

class TestDataValidation:
    def test_data_quality_checks(self):
        """Test data quality validation"""
        data = generate_training_data(num_engines=2, cycles_per_engine=20)
        
        # Check for null values
        assert not data.isnull().any().any()
        
        # Check data types
        assert data['engine_id'].dtype == 'object'
        assert data['cycle'].dtype in ['int64', 'int32']
        assert data['rul'].dtype in ['int64', 'int32', 'float64']
        
        # Check value ranges
        assert data['cycle'].min() >= 1
        assert data['rul'].min() >= 0
        
        # Check sensor value ranges (should be realistic)
        for col in data.columns:
            if col.startswith('sensor_'):
                assert not data[col].isnull().any()
                assert np.isfinite(data[col]).all()
