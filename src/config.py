"""
Configuration settings for different environments
"""
import os
from typing import Dict, Any

class Config:
    """Base configuration class"""
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'engine-sensor-data')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5433/engine_monitoring')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    
    # ML Model Configuration
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Use local services
    KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
    DATABASE_URL = 'postgresql://postgres:password@localhost:5433/engine_monitoring'
    REDIS_HOST = 'localhost'
    
class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Use test databases
    DATABASE_URL = 'postgresql://postgres:password@localhost:5433/engine_monitoring_test'
    KAFKA_TOPIC = 'engine-sensor-data-test'
    
class StagingConfig(Config):
    """Staging environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Use staging services
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('STAGING_KAFKA_SERVERS', 'kafka-staging:9092')
    DATABASE_URL = os.getenv('STAGING_DATABASE_URL')
    REDIS_HOST = os.getenv('STAGING_REDIS_HOST', 'redis-staging')

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Use production services
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('PRODUCTION_KAFKA_SERVERS')
    DATABASE_URL = os.getenv('PRODUCTION_DATABASE_URL')
    REDIS_HOST = os.getenv('PRODUCTION_REDIS_HOST')
    
    # Production security settings
    SSL_REQUIRED = True
    SECRET_KEY = os.getenv('SECRET_KEY')

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(env: str = None) -> Config:
    """Get configuration for specified environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'default')
    
    return config.get(env, config['default'])()
