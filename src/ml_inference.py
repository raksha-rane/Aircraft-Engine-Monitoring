"""
Real-time ML Inference System
Integrates ML models with streaming data for live predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
sys.path.append('src')

from ml_models import EngineHealthPredictor
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json
import time

class RealTimeMLInference:
    """
    Real-time machine learning inference for engine monitoring
    """
    
    def __init__(self):
        self.predictor = EngineHealthPredictor()
        self.db_conn = None
        self.redis_client = None
        self._connect_services()
        self._load_models()
        
    def _connect_services(self):
        """Connect to database and Redis"""
        try:
            # PostgreSQL connection
            self.db_conn = psycopg2.connect(
                host='localhost',
                port=5433,
                dbname='engine_monitoring',
                user='postgres',
                password='password'
            )
            print("✅ Connected to PostgreSQL")
            
            # Redis connection
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            print("✅ Connected to Redis")
            
        except Exception as e:
            print(f"❌ Service connection error: {e}")
            raise
    
    def _load_models(self):
        """Load trained ML models"""
        if not self.predictor.load_models():
            print("🤖 Models not found. Training new models...")
            self._train_models()
    
    def _train_models(self):
        """Train models if not available"""
        from ml_models import generate_training_data
        
        training_data = generate_training_data()
        self.predictor.train_rul_model(training_data)
        self.predictor.train_anomaly_model(training_data)
        self.predictor.save_models()
    
    def get_recent_sensor_data(self, hours=1, min_cycles=10):
        """
        Fetch recent sensor data from database
        """
        query = """
        SELECT 
            engine_id,
            timestamp,
            cycle,
            health_state,
            remaining_useful_life,
            sensor_data
        FROM sensor_readings 
        WHERE timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY engine_id, cycle
        """
        
        try:
            df = pd.read_sql_query(query, self.db_conn, params=[hours])
            
            if df.empty:
                print("⚠️ No recent data found")
                return None
            
            # Parse sensor data from JSONB
            sensor_columns = []
            for idx, row in df.iterrows():
                sensor_data = json.loads(row['sensor_data']) if isinstance(row['sensor_data'], str) else row['sensor_data']
                for sensor_id, value in sensor_data.items():
                    df.at[idx, sensor_id] = value
                    if sensor_id not in sensor_columns:
                        sensor_columns.append(sensor_id)
            
            # Filter engines with minimum cycles
            engine_cycle_counts = df.groupby('engine_id')['cycle'].count()
            valid_engines = engine_cycle_counts[engine_cycle_counts >= min_cycles].index
            df = df[df['engine_id'].isin(valid_engines)]
            
            print(f"📊 Loaded {len(df)} records from {df['engine_id'].nunique()} engines")
            return df
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
            return None
    
    def run_ml_inference(self, df):
        """
        Run ML inference on sensor data
        """
        if df is None or df.empty:
            return None
        
        results = []
        
        for engine_id in df['engine_id'].unique():
            engine_data = df[df['engine_id'] == engine_id].sort_values('cycle')
            
            try:
                # Get latest data for prediction
                latest_data = engine_data.tail(5)  # Use last 5 cycles
                
                # RUL Prediction
                predicted_rul = self.predictor.predict_rul(latest_data)
                if predicted_rul is not None and len(predicted_rul) > 0:
                    avg_predicted_rul = np.nanmean(predicted_rul)
                else:
                    avg_predicted_rul = np.nan
                
                # Anomaly Detection
                anomaly_scores, anomaly_preds = self.predictor.detect_anomalies(latest_data)
                if anomaly_scores is not None and anomaly_preds is not None:
                    anomaly_ratio = (anomaly_preds == -1).sum() / len(anomaly_preds)
                    avg_anomaly_score = np.mean(anomaly_scores)
                else:
                    anomaly_ratio = 0
                    avg_anomaly_score = 0
                
                # Current health metrics
                latest_cycle = engine_data['cycle'].max()
                current_health = engine_data['health_state'].iloc[-1]
                actual_rul = engine_data['remaining_useful_life'].iloc[-1]
                
                # Calculate prediction accuracy
                rul_error = abs(avg_predicted_rul - actual_rul) if not np.isnan(avg_predicted_rul) else np.inf
                
                # Determine warning status
                warning_level = "GREEN"
                maintenance_priority = "LOW"
                
                if avg_predicted_rul < 30:  # Less than 30 cycles
                    warning_level = "YELLOW"
                    maintenance_priority = "MEDIUM"
                
                if avg_predicted_rul < 15 or anomaly_ratio > 0.6:  # Less than 15 cycles or high anomalies
                    warning_level = "RED"
                    maintenance_priority = "HIGH"
                
                # Early warning (15-30 cycles ahead)
                early_warning = avg_predicted_rul < 30 and avg_predicted_rul > 15
                critical_warning = avg_predicted_rul < 15
                
                result = {
                    'engine_id': engine_id,
                    'timestamp': datetime.now().isoformat(),
                    'current_cycle': latest_cycle,
                    'current_health_state': current_health,
                    'actual_rul': actual_rul,
                    'predicted_rul': round(avg_predicted_rul, 1) if not np.isnan(avg_predicted_rul) else None,
                    'rul_prediction_error': round(rul_error, 1) if not np.isinf(rul_error) else None,
                    'anomaly_score': round(avg_anomaly_score, 3),
                    'anomaly_ratio': round(anomaly_ratio, 3),
                    'warning_level': warning_level,
                    'maintenance_priority': maintenance_priority,
                    'early_warning_15_30_cycles': early_warning,
                    'critical_warning_under_15_cycles': critical_warning,
                    'maintenance_recommended': warning_level in ["YELLOW", "RED"]
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"❌ ML inference error for {engine_id}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def cache_ml_results(self, results_df):
        """
        Cache ML results in Redis for dashboard access
        """
        if results_df is None or results_df.empty:
            return
        
        try:
            # Cache individual engine predictions
            for _, row in results_df.iterrows():
                cache_key = f"ml_prediction:{row['engine_id']}"
                cache_data = row.to_dict()
                self.redis_client.setex(cache_key, 3600, json.dumps(cache_data))  # 1 hour TTL
            
            # Cache fleet summary
            fleet_summary = {
                'timestamp': datetime.now().isoformat(),
                'total_engines': len(results_df),
                'engines_by_warning': results_df['warning_level'].value_counts().to_dict(),
                'engines_needing_maintenance': len(results_df[results_df['maintenance_recommended']]),
                'early_warnings_15_30_cycles': len(results_df[results_df['early_warning_15_30_cycles']]),
                'critical_warnings_under_15_cycles': len(results_df[results_df['critical_warning_under_15_cycles']]),
                'avg_predicted_rul': results_df['predicted_rul'].mean(),
                'avg_anomaly_score': results_df['anomaly_score'].mean()
            }
            
            self.redis_client.setex('ml_fleet_summary', 3600, json.dumps(fleet_summary))
            print(f"✅ Cached ML results for {len(results_df)} engines")
            
        except Exception as e:
            print(f"❌ Cache error: {e}")
    
    def generate_maintenance_recommendations(self, results_df):
        """
        Generate specific maintenance recommendations
        """
        if results_df is None or results_df.empty:
            return []
        
        recommendations = []
        
        for _, row in results_df.iterrows():
            engine_id = row['engine_id']
            
            if row['critical_warning_under_15_cycles']:
                recommendations.append({
                    'engine_id': engine_id,
                    'priority': 'CRITICAL',
                    'action': 'IMMEDIATE_INSPECTION',
                    'reason': f"Predicted failure in {row['predicted_rul']:.0f} cycles",
                    'estimated_downtime_reduction': '40%'
                })
            
            elif row['early_warning_15_30_cycles']:
                recommendations.append({
                    'engine_id': engine_id,
                    'priority': 'HIGH',
                    'action': 'SCHEDULE_MAINTENANCE',
                    'reason': f"Early warning: {row['predicted_rul']:.0f} cycles remaining",
                    'estimated_downtime_reduction': '25%'
                })
            
            elif row['anomaly_ratio'] > 0.4:
                recommendations.append({
                    'engine_id': engine_id,
                    'priority': 'MEDIUM',
                    'action': 'DIAGNOSTIC_CHECK',
                    'reason': f"Anomaly detection: {row['anomaly_ratio']:.1%} anomalous readings",
                    'estimated_downtime_reduction': '15%'
                })
        
        return recommendations
    
    def run_continuous_inference(self, interval_minutes=5):
        """
        Run continuous ML inference on streaming data
        """
        print(f"🔄 Starting continuous ML inference (every {interval_minutes} minutes)")
        
        while True:
            try:
                print(f"\n🤖 Running ML inference at {datetime.now().strftime('%H:%M:%S')}")
                
                # Get recent data
                df = self.get_recent_sensor_data(hours=2)
                
                if df is not None:
                    # Run ML inference
                    results = self.run_ml_inference(df)
                    
                    if results is not None and not results.empty:
                        # Cache results
                        self.cache_ml_results(results)
                        
                        # Generate recommendations
                        recommendations = self.generate_maintenance_recommendations(results)
                        
                        # Print summary
                        print(f"📊 ML Inference Summary:")
                        print(f"   Engines analyzed: {len(results)}")
                        print(f"   Early warnings (15-30 cycles): {len(results[results['early_warning_15_30_cycles']])}")
                        print(f"   Critical warnings (<15 cycles): {len(results[results['critical_warning_under_15_cycles']])}")
                        print(f"   Maintenance recommendations: {len(recommendations)}")
                        
                        if recommendations:
                            print(f"🚨 Active Recommendations:")
                            for rec in recommendations[:3]:  # Show top 3
                                print(f"   {rec['engine_id']}: {rec['action']} ({rec['priority']})")
                
                # Wait for next iteration
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n⏹️ ML inference stopped by user")
                break
            except Exception as e:
                print(f"❌ ML inference error: {e}")
                time.sleep(30)  # Wait 30 seconds before retry
    
    def close(self):
        """Close connections"""
        if self.db_conn:
            self.db_conn.close()
        print("✅ ML inference system closed")

def main():
    """Main function for running ML inference"""
    print("🤖 Real-time ML Inference System")
    print("=" * 40)
    
    try:
        ml_system = RealTimeMLInference()
        
        # Run one-time inference
        print("\n🔍 Running one-time ML analysis...")
        df = ml_system.get_recent_sensor_data(hours=24)
        
        if df is not None:
            results = ml_system.run_ml_inference(df)
            
            if results is not None and not results.empty:
                ml_system.cache_ml_results(results)
                recommendations = ml_system.generate_maintenance_recommendations(results)
                
                print(f"\n📊 Analysis Complete:")
                print(f"   Total engines: {len(results)}")
                print(f"   Avg predicted RUL: {results['predicted_rul'].mean():.1f} cycles")
                print(f"   Early warnings: {len(results[results['early_warning_15_30_cycles']])} engines")
                print(f"   Critical warnings: {len(results[results['critical_warning_under_15_cycles']])} engines")
                
                # Display results
                print(f"\n📋 Engine Status Summary:")
                display_cols = ['engine_id', 'predicted_rul', 'warning_level', 'maintenance_priority']
                print(results[display_cols].to_string(index=False))
                
                if recommendations:
                    print(f"\n🔧 Maintenance Recommendations:")
                    for rec in recommendations:
                        print(f"   {rec['engine_id']}: {rec['action']} - {rec['reason']}")
        
        # Ask if user wants continuous monitoring
        user_input = input("\n🔄 Start continuous ML monitoring? (y/n): ").lower().strip()
        if user_input == 'y':
            ml_system.run_continuous_inference(interval_minutes=2)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'ml_system' in locals():
            ml_system.close()

if __name__ == "__main__":
    main()
