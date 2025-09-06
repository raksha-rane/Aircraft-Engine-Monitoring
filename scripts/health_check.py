#!/usr/bin/env python3
"""
Health check script for all system components
Usage: python scripts/health_check.py
"""

import sys
import os
import json
import requests
import psycopg2
import redis
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import get_config

class HealthChecker:
    def __init__(self, environment='development'):
        self.config = get_config(environment)
        self.results = []
    
    def check_kafka(self):
        """Check Kafka connectivity"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=[self.config.KAFKA_BOOTSTRAP_SERVERS],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=5000
            )
            
            # Send test message
            test_message = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "health_check": "kafka"
            }
            
            future = producer.send(self.config.KAFKA_TOPIC, test_message)
            producer.flush(timeout=5)
            
            self.results.append({
                "service": "Kafka",
                "status": "✅ HEALTHY",
                "details": f"Connected to {self.config.KAFKA_BOOTSTRAP_SERVERS}"
            })
            
            producer.close()
            return True
            
        except Exception as e:
            self.results.append({
                "service": "Kafka",
                "status": "❌ UNHEALTHY",
                "details": f"Error: {str(e)}"
            })
            return False
    
    def check_postgresql(self):
        """Check PostgreSQL connectivity"""
        try:
            conn = psycopg2.connect(self.config.DATABASE_URL)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Check if our table exists
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'engine_sensor_data';
            """)
            table_exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            self.results.append({
                "service": "PostgreSQL",
                "status": "✅ HEALTHY",
                "details": f"Connected. Table exists: {table_exists}"
            })
            return True
            
        except Exception as e:
            self.results.append({
                "service": "PostgreSQL",
                "status": "❌ UNHEALTHY",
                "details": f"Error: {str(e)}"
            })
            return False
    
    def check_redis(self):
        """Check Redis connectivity"""
        try:
            r = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                decode_responses=True
            )
            
            # Test ping
            pong = r.ping()
            
            # Test set/get
            test_key = "health_check"
            test_value = datetime.now().isoformat()
            r.setex(test_key, 60, test_value)  # Expire in 60 seconds
            retrieved = r.get(test_key)
            
            self.results.append({
                "service": "Redis",
                "status": "✅ HEALTHY",
                "details": f"Ping: {pong}, Set/Get: {'OK' if retrieved == test_value else 'FAILED'}"
            })
            return True
            
        except Exception as e:
            self.results.append({
                "service": "Redis",
                "status": "❌ UNHEALTHY",
                "details": f"Error: {str(e)}"
            })
            return False
    
    def check_models(self):
        """Check ML models availability"""
        try:
            model_path = self.config.MODEL_PATH
            required_models = [
                'rul_model.pkl',
                'anomaly_model.pkl',
                'scaler.pkl',
                'feature_columns.pkl'
            ]
            
            missing_models = []
            for model_file in required_models:
                full_path = os.path.join(model_path, model_file)
                if not os.path.exists(full_path):
                    missing_models.append(model_file)
            
            if not missing_models:
                self.results.append({
                    "service": "ML Models",
                    "status": "✅ HEALTHY",
                    "details": f"All models found in {model_path}"
                })
                return True
            else:
                self.results.append({
                    "service": "ML Models",
                    "status": "⚠️ PARTIAL",
                    "details": f"Missing: {', '.join(missing_models)}"
                })
                return False
                
        except Exception as e:
            self.results.append({
                "service": "ML Models",
                "status": "❌ UNHEALTHY",
                "details": f"Error: {str(e)}"
            })
            return False
    
    def check_streamlit_dashboard(self):
        """Check if Streamlit dashboard is accessible"""
        try:
            # Try to connect to Streamlit (usually on port 8501)
            dashboard_url = "http://localhost:8501"
            response = requests.get(f"{dashboard_url}/healthz", timeout=5)
            
            if response.status_code == 200:
                self.results.append({
                    "service": "Streamlit Dashboard",
                    "status": "✅ HEALTHY",
                    "details": f"Accessible at {dashboard_url}"
                })
                return True
            else:
                self.results.append({
                    "service": "Streamlit Dashboard",
                    "status": "❌ UNHEALTHY",
                    "details": f"HTTP {response.status_code}"
                })
                return False
                
        except requests.exceptions.ConnectionError:
            self.results.append({
                "service": "Streamlit Dashboard",
                "status": "❌ UNHEALTHY",
                "details": "Connection refused - service may not be running"
            })
            return False
        except Exception as e:
            self.results.append({
                "service": "Streamlit Dashboard",
                "status": "❌ UNHEALTHY",
                "details": f"Error: {str(e)}"
            })
            return False
    
    def run_all_checks(self):
        """Run all health checks"""
        print("🏥 Aircraft Engine Monitoring - Health Check")
        print("=" * 50)
        print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        checks = [
            ("Kafka", self.check_kafka),
            ("PostgreSQL", self.check_postgresql),
            ("Redis", self.check_redis),
            ("ML Models", self.check_models),
            ("Streamlit Dashboard", self.check_streamlit_dashboard)
        ]
        
        healthy_count = 0
        total_checks = len(checks)
        
        for name, check_func in checks:
            print(f"Checking {name}...", end=" ")
            if check_func():
                healthy_count += 1
            print()
        
        print("\n" + "=" * 50)
        print("📊 HEALTH CHECK SUMMARY")
        print("=" * 50)
        
        for result in self.results:
            print(f"{result['service']:<20} {result['status']}")
            if result['details']:
                print(f"{'':>21} {result['details']}")
            print()
        
        overall_health = "✅ HEALTHY" if healthy_count == total_checks else f"⚠️ {healthy_count}/{total_checks} HEALTHY"
        print(f"Overall System Health: {overall_health}")
        
        # Return exit code for CI/CD
        return 0 if healthy_count == total_checks else 1

def main():
    environment = os.getenv('FLASK_ENV', 'development')
    checker = HealthChecker(environment)
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
