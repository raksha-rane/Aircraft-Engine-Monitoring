"""
Machine Learning Models for Aircraft Engine Monitoring
Implements RUL prediction and anomaly detection for predictive maintenance
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class EngineHealthPredictor:
    """
    Machine Learning predictor for engine health monitoring
    Implements RUL prediction and anomaly detection
    """
    
    def __init__(self):
        self.rul_model = None
        self.anomaly_model = None
        self.feature_columns = None
        self.models_dir = "models/"
        
        # Create models directory if it doesn't exist
        os.makedirs(self.models_dir, exist_ok=True)
    
    def prepare_features(self, data):
        """
        Engineer features for ML models
        """
        df = data.copy()
        
        # Ensure we have required columns
        required_cols = ['cycle', 'engine_id']
        for col in required_cols:
            if col not in df.columns:
                print(f"Warning: {col} not found in data")
                return df
        
        # Sort by engine and cycle
        df = df.sort_values(['engine_id', 'cycle'])
        
        # Normalize cycle (important for RUL prediction)
        df['cycle_normalized'] = df.groupby('engine_id')['cycle'].transform(
            lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0
        )
        
        # Get sensor columns (assuming they start with 'sensor_')
        sensor_cols = [col for col in df.columns if 'sensor_' in col and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
        
        if len(sensor_cols) == 0:
            print("Warning: No numeric sensor columns found")
            return df
        
        # Rolling statistics for each sensor
        for sensor in sensor_cols:
            if sensor in df.columns:
                # Rolling mean and std (window of 3 cycles)
                df[f'{sensor}_rolling_mean'] = df.groupby('engine_id')[sensor].transform(
                    lambda x: x.rolling(window=3, min_periods=1).mean()
                )
                df[f'{sensor}_rolling_std'] = df.groupby('engine_id')[sensor].transform(
                    lambda x: x.rolling(window=3, min_periods=1).std().fillna(0)
                )
        
        # Drop any infinite or extremely large values
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN values only for numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        
        return df
    
    def train_rul_model(self, training_data):
        """
        Train RUL (Remaining Useful Life) prediction model
        """
        print("🤖 Training RUL Prediction Model...")
        
        # Prepare features
        df = self.prepare_features(training_data)
        
        # Feature columns (exclude target and ID columns)
        exclude_cols = ['engine_id', 'remaining_useful_life', 'health_state', 'timestamp']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Ensure we have the target column
        if 'remaining_useful_life' not in df.columns:
            print("❌ Error: 'remaining_useful_life' column not found")
            return False
        
        # Prepare training data
        X = df[feature_cols]
        y = df['remaining_useful_life']
        
        # Remove any rows with NaN in target
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]
        
        if len(X) == 0:
            print("❌ Error: No valid training data")
            return False
        
        # Store feature columns
        self.feature_columns = feature_cols
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest model
        self.rul_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.rul_model.fit(X_train, y_train)
        
        # Evaluate model
        train_pred = self.rul_model.predict(X_train)
        test_pred = self.rul_model.predict(X_test)
        
        train_mse = mean_squared_error(y_train, train_pred)
        test_mse = mean_squared_error(y_test, test_pred)
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)
        
        print(f"✅ RUL Model Training Complete:")
        print(f"   Training MSE: {train_mse:.2f}, MAE: {train_mae:.2f}, R²: {train_r2:.3f}")
        print(f"   Test MSE: {test_mse:.2f}, MAE: {test_mae:.2f}, R²: {test_r2:.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.rul_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"   Top 5 Features:")
        for _, row in feature_importance.head().iterrows():
            print(f"     {row['feature']}: {row['importance']:.3f}")
        
        return True
    
    def train_anomaly_model(self, training_data):
        """
        Train anomaly detection model
        """
        print("\n🔍 Training Anomaly Detection Model...")
        
        # Prepare features
        df = self.prepare_features(training_data)
        
        # Use same feature columns as RUL model
        if self.feature_columns is None:
            print("❌ Error: Train RUL model first")
            return False
        
        # Prepare training data
        X = df[self.feature_columns]
        
        # Remove NaN values
        X = X.fillna(X.median())
        
        # Train Isolation Forest
        self.anomaly_model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_jobs=-1
        )
        
        self.anomaly_model.fit(X)
        
        # Evaluate on training data
        anomaly_pred = self.anomaly_model.predict(X)
        anomaly_scores = self.anomaly_model.score_samples(X)
        
        n_anomalies = (anomaly_pred == -1).sum()
        anomaly_rate = n_anomalies / len(anomaly_pred) * 100
        
        print(f"✅ Anomaly Detection Training Complete:")
        print(f"   Total samples: {len(X)}")
        print(f"   Anomalies detected: {n_anomalies} ({anomaly_rate:.1f}%)")
        print(f"   Anomaly score range: [{anomaly_scores.min():.3f}, {anomaly_scores.max():.3f}]")
        
        return True
    
    def predict_rul(self, data):
        """
        Predict Remaining Useful Life
        """
        if self.rul_model is None:
            print("❌ RUL model not trained")
            return None
        
        df = self.prepare_features(data)
        
        # Ensure all feature columns exist
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            print(f"❌ Missing columns: {missing_cols}")
            return None
        
        X = df[self.feature_columns].fillna(0)
        predictions = self.rul_model.predict(X)
        
        return predictions
    
    def detect_anomalies(self, data):
        """
        Detect anomalies in sensor data
        """
        if self.anomaly_model is None:
            print("❌ Anomaly model not trained")
            return None, None
        
        df = self.prepare_features(data)
        
        # Ensure all feature columns exist
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            print(f"❌ Missing columns: {missing_cols}")
            return None, None
        
        X = df[self.feature_columns].fillna(0)
        
        anomaly_scores = self.anomaly_model.score_samples(X)
        anomaly_predictions = self.anomaly_model.predict(X)
        
        return anomaly_scores, anomaly_predictions
    
    def early_warning_system(self, data):
        """
        Generate early warnings for maintenance (15-30 cycles ahead)
        """
        results = []
        
        for engine_id in data['engine_id'].unique():
            engine_data = data[data['engine_id'] == engine_id]
            
            # Get predictions
            rul_pred = self.predict_rul(engine_data)
            anomaly_scores, anomaly_preds = self.detect_anomalies(engine_data)
            
            if rul_pred is not None and len(rul_pred) > 0:
                avg_rul = np.mean(rul_pred)
                
                # Anomaly ratio
                anomaly_ratio = (anomaly_preds == -1).sum() / len(anomaly_preds) if anomaly_preds is not None else 0
                
                # Determine warning level
                warning_level = "GREEN"
                maintenance_action = "ROUTINE_MONITORING"
                
                if avg_rul <= 30 and avg_rul > 15:  # Early warning (15-30 cycles)
                    warning_level = "YELLOW"
                    maintenance_action = "SCHEDULE_MAINTENANCE"
                elif avg_rul <= 15:  # Critical warning
                    warning_level = "RED"
                    maintenance_action = "IMMEDIATE_INSPECTION"
                elif anomaly_ratio > 0.5:  # High anomaly rate
                    warning_level = "YELLOW"
                    maintenance_action = "DIAGNOSTIC_CHECK"
                
                results.append({
                    'engine_id': engine_id,
                    'predicted_rul': avg_rul,
                    'anomaly_ratio': anomaly_ratio,
                    'warning_level': warning_level,
                    'maintenance_action': maintenance_action,
                    'early_warning_15_30_cycles': 15 < avg_rul <= 30,
                    'critical_warning_under_15_cycles': avg_rul <= 15
                })
        
        return results
    
    def save_models(self):
        """
        Save trained models to disk
        """
        try:
            if self.rul_model:
                with open(f"{self.models_dir}/rul_model.pkl", 'wb') as f:
                    pickle.dump(self.rul_model, f)
            
            if self.anomaly_model:
                with open(f"{self.models_dir}/anomaly_model.pkl", 'wb') as f:
                    pickle.dump(self.anomaly_model, f)
            
            if self.feature_columns:
                with open(f"{self.models_dir}/feature_columns.pkl", 'wb') as f:
                    pickle.dump(self.feature_columns, f)
            
            print(f"✅ Models saved to {self.models_dir}")
            return True
        except Exception as e:
            print(f"❌ Error saving models: {e}")
            return False
    
    def load_models(self):
        """
        Load trained models from disk
        """
        try:
            rul_path = f"{self.models_dir}/rul_model.pkl"
            anomaly_path = f"{self.models_dir}/anomaly_model.pkl"
            features_path = f"{self.models_dir}/feature_columns.pkl"
            
            if os.path.exists(rul_path):
                with open(rul_path, 'rb') as f:
                    self.rul_model = pickle.load(f)
            
            if os.path.exists(anomaly_path):
                with open(anomaly_path, 'rb') as f:
                    self.anomaly_model = pickle.load(f)
            
            if os.path.exists(features_path):
                with open(features_path, 'rb') as f:
                    self.feature_columns = pickle.load(f)
            
            if self.rul_model and self.anomaly_model:
                print("✅ Models loaded successfully")
                return True
            else:
                print("⚠️ Some models not found")
                return False
                
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False

def generate_training_data(num_engines=15, cycles_per_engine=100):
    """
    Generate realistic training data using NASA C-MAPSS style sensors
    """
    print(f"📊 Generating training data for {num_engines} engines...")
    
    all_data = []
    
    for engine_id in range(1, num_engines + 1):
        engine_name = f"RR_TRENT_{1000 + engine_id}"
        
        # Random failure point (50-150 cycles)
        failure_cycle = np.random.randint(50, 150)
        
        for cycle in range(1, min(cycles_per_engine, failure_cycle) + 1):
            # Calculate remaining useful life
            rul = failure_cycle - cycle
            
            # Health state based on RUL
            if rul > 50:
                health_state = "HEALTHY"
            elif rul > 20:
                health_state = "DEGRADING"
            elif rul > 5:
                health_state = "CRITICAL"
            else:
                health_state = "FAILED"
            
            # Generate realistic sensor data with degradation
            degradation_factor = max(0, (failure_cycle - cycle) / failure_cycle)
            noise = np.random.normal(0, 0.1)
            
            # NASA C-MAPSS style sensors (21 sensors)
            sensor_data = {
                'sensor_1': 518.67 + np.random.normal(0, 2),  # Fan inlet temperature
                'sensor_2': 641.82 + (1 - degradation_factor) * 50 + noise * 10,  # LPC outlet temperature
                'sensor_3': 1589.70 + (1 - degradation_factor) * 100 + noise * 20,  # HPC outlet temperature
                'sensor_4': 1400.60 + (1 - degradation_factor) * 80 + noise * 15,  # LPT outlet temperature
                'sensor_5': 14.62 + np.random.normal(0, 0.5),  # Fan inlet pressure
                'sensor_6': 21.61 + np.random.normal(0, 1),  # bypass-duct pressure
                'sensor_7': 554.36 + (1 - degradation_factor) * 30 + noise * 8,  # HPC outlet pressure
                'sensor_8': 2388.02 + degradation_factor * 200 + noise * 50,  # Physical fan speed
                'sensor_9': 9046.19 + degradation_factor * 500 + noise * 100,  # Physical core speed
                'sensor_10': 1.30 + np.random.normal(0, 0.1),  # Engine pressure ratio
                'sensor_11': 47.47 + degradation_factor * 20 + noise * 5,  # Static pressure at HPC outlet
                'sensor_12': 521.66 + np.random.normal(0, 2),  # Ratio of fuel flow to Ps30
                'sensor_13': 2388.02 + degradation_factor * 200 + noise * 50,  # Corrected fan speed
                'sensor_14': 8138.62 + degradation_factor * 400 + noise * 80,  # Corrected core speed
                'sensor_15': 8.4195 + degradation_factor * 2 + noise * 0.5,  # Bypass Ratio
                'sensor_16': 0.03 + np.random.normal(0, 0.005),  # Burner fuel-air ratio
                'sensor_17': 392.0 + degradation_factor * 50 + noise * 10,  # Bleed Enthalpy
                'sensor_18': 2388.0 + degradation_factor * 200 + noise * 50,  # Required fan speed
                'sensor_19': 100.0 + degradation_factor * 30 + noise * 8,  # Required fan conversion speed
                'sensor_20': 38.86 + degradation_factor * 10 + noise * 3,  # High pressure turbines Cool air flow
                'sensor_21': 23.419 + degradation_factor * 8 + noise * 2,  # Low pressure turbines Cool air flow
            }
            
            record = {
                'engine_id': engine_name,
                'cycle': cycle,
                'timestamp': datetime.now(),
                'health_state': health_state,
                'remaining_useful_life': rul,
                **sensor_data
            }
            
            all_data.append(record)
    
    df = pd.DataFrame(all_data)
    print(f"✅ Generated {len(df)} training samples for {num_engines} engines")
    return df

def main():
    """
    Main function for training ML models
    """
    print("🤖 Aircraft Engine ML Training Pipeline")
    print("=" * 45)
    
    # Generate training data
    training_data = generate_training_data(num_engines=15, cycles_per_engine=100)
    
    # Initialize predictor
    predictor = EngineHealthPredictor()
    
    # Train models
    if predictor.train_rul_model(training_data):
        if predictor.train_anomaly_model(training_data):
            # Save models
            predictor.save_models()
            
            # Test early warning system
            print("\n🚨 Testing Early Warning System:")
            warnings = predictor.early_warning_system(training_data.tail(50))
            
            for warning in warnings[-5:]:  # Show last 5
                status = warning['warning_level']
                emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}[status]
                print(f"   {emoji} {warning['engine_id']}: RUL={warning['predicted_rul']:.1f}, Action={warning['maintenance_action']}")
            
            print(f"\n✅ ML Pipeline Complete!")
            print(f"   Early warnings (15-30 cycles): {sum(w['early_warning_15_30_cycles'] for w in warnings)} engines")
            print(f"   Critical warnings (<15 cycles): {sum(w['critical_warning_under_15_cycles'] for w in warnings)} engines")
        else:
            print("❌ Anomaly model training failed")
    else:
        print("❌ RUL model training failed")

if __name__ == "__main__":
    main()
