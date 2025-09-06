"""
Kafka Consumer for Engine Sensor Data
Consumes streaming sensor data and stores in PostgreSQL
"""

import json
import logging
import os
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from typing import Dict, List
from urllib.parse import urlparse

# Import configuration
from config import get_config

# Get configuration
config = get_config()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database operations"""
    
    def __init__(self, database_url=None):
        if database_url is None:
            database_url = config.DATABASE_URL
            
        # Parse database URL
        parsed = urlparse(database_url)
        self.connection_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'dbname': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password
        }
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to PostgreSQL"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(**self.connection_params)
                self.conn.autocommit = True
                logger.info("✅ Connected to PostgreSQL successfully")
                return
            except Exception as e:
                logger.warning(f"⚠️  Database connection attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                else:
                    logger.error("❌ Failed to connect to database after all retries")
                    raise
    
    def _create_tables(self):
        """Create necessary database tables"""
        try:
            with self.conn.cursor() as cursor:
                # Main sensor readings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_readings (
                        id SERIAL PRIMARY KEY,
                        engine_id VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        cycle INTEGER NOT NULL,
                        health_state VARCHAR(20) NOT NULL,
                        remaining_useful_life INTEGER,
                        sensor_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create indexes separately
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sensor_readings_engine_time 
                    ON sensor_readings (engine_id, timestamp);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sensor_readings_health 
                    ON sensor_readings (health_state);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sensor_readings_cycle 
                    ON sensor_readings (cycle);
                """)
                
                # Alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        engine_id VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        sensor_name VARCHAR(50) NOT NULL,
                        current_value FLOAT NOT NULL,
                        threshold_value FLOAT NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create indexes for alerts table
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_alerts_engine_time 
                    ON alerts (engine_id, timestamp);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_alerts_severity 
                    ON alerts (severity, resolved);
                """)
                
                # Engine status summary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS engine_status (
                        engine_id VARCHAR(50) PRIMARY KEY,
                        current_health_state VARCHAR(20) NOT NULL,
                        last_reading_timestamp TIMESTAMP NOT NULL,
                        total_cycles INTEGER NOT NULL,
                        remaining_useful_life INTEGER,
                        active_alerts_count INTEGER DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                logger.info("✅ Database tables created/verified")
                
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    def store_reading(self, reading: Dict):
        """Store a sensor reading in the database"""
        try:
            with self.conn.cursor() as cursor:
                # Insert sensor reading
                cursor.execute("""
                    INSERT INTO sensor_readings 
                    (engine_id, timestamp, cycle, health_state, remaining_useful_life, sensor_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    reading['engine_id'],
                    reading['timestamp'],
                    reading['cycle'],
                    reading['health_state'],
                    reading['remaining_useful_life'],
                    json.dumps(reading['sensors'])
                ))
                
                # Store alerts if any
                for alert in reading.get('alerts', []):
                    cursor.execute("""
                        INSERT INTO alerts 
                        (engine_id, timestamp, sensor_name, current_value, threshold_value, severity)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        reading['engine_id'],
                        reading['timestamp'],
                        alert['sensor_name'],
                        alert['current_value'],
                        alert['threshold'],
                        alert['severity']
                    ))
                
                # Update engine status summary
                cursor.execute("""
                    INSERT INTO engine_status 
                    (engine_id, current_health_state, last_reading_timestamp, 
                     total_cycles, remaining_useful_life, active_alerts_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (engine_id) 
                    DO UPDATE SET
                        current_health_state = EXCLUDED.current_health_state,
                        last_reading_timestamp = EXCLUDED.last_reading_timestamp,
                        total_cycles = EXCLUDED.total_cycles,
                        remaining_useful_life = EXCLUDED.remaining_useful_life,
                        active_alerts_count = EXCLUDED.active_alerts_count,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    reading['engine_id'],
                    reading['health_state'],
                    reading['timestamp'],
                    reading['cycle'],
                    reading['remaining_useful_life'],
                    len(reading.get('alerts', []))
                ))
                
        except Exception as e:
            logger.error(f"❌ Failed to store reading for {reading.get('engine_id', 'unknown')}: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")

class RedisCache:
    """Redis cache for recent data and alerts"""
    
    def __init__(self, host=None, port=None, db=0):
        if host is None:
            host = config.REDIS_HOST
        if port is None:
            port = config.REDIS_PORT
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            logger.info("✅ Connected to Redis successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def cache_latest_reading(self, engine_id: str, reading: Dict):
        """Cache the latest reading for an engine"""
        try:
            # Store latest reading (expires in 1 hour)
            self.redis_client.setex(
                f"latest:{engine_id}",
                3600,  # 1 hour TTL
                json.dumps(reading)
            )
            
            # Store in recent readings list (keep last 100)
            self.redis_client.lpush(f"recent:{engine_id}", json.dumps(reading))
            self.redis_client.ltrim(f"recent:{engine_id}", 0, 99)  # Keep only last 100
            
        except Exception as e:
            logger.error(f"❌ Failed to cache reading for {engine_id}: {e}")
    
    def cache_alert(self, alert: Dict):
        """Cache active alerts"""
        try:
            alert_key = f"alert:{alert['engine_id']}:{alert['sensor_name']}"
            self.redis_client.setex(alert_key, 1800, json.dumps(alert))  # 30 min TTL
        except Exception as e:
            logger.error(f"❌ Failed to cache alert: {e}")

class EngineSensorConsumer:
    """Kafka consumer that processes engine sensor data"""
    
    def __init__(self, bootstrap_servers=None, topic=None):
        self.topic = topic or config.KAFKA_TOPIC
        self.consumer = None
        self.db_manager = DatabaseManager()
        self.cache = RedisCache()
        
        # Parse bootstrap servers from config
        if bootstrap_servers is None:
            bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [server.strip() for server in bootstrap_servers.split(',')]
        
        self._connect_to_kafka(bootstrap_servers)
    
    def _connect_to_kafka(self, bootstrap_servers):
        """Initialize Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8'),
                group_id='engine-monitoring-group',
                auto_offset_reset='latest',  # Start from latest messages
                enable_auto_commit=True
            )
            logger.info(f"✅ Connected to Kafka consumer for topic '{self.topic}'")
        except Exception as e:
            logger.error(f"❌ Failed to create Kafka consumer: {e}")
            raise
    
    def process_reading(self, reading: Dict):
        """Process a single engine reading"""
        try:
            engine_id = reading['engine_id']
            
            # Store in database
            self.db_manager.store_reading(reading)
            
            # Cache in Redis
            self.cache.cache_latest_reading(engine_id, reading)
            
            # Cache any alerts
            for alert in reading.get('alerts', []):
                self.cache.cache_alert(alert)
            
            # Log important events
            if reading['health_state'] != 'healthy':
                logger.warning(f"⚠️  {engine_id}: {reading['health_state']} state detected")
            
            if reading.get('alerts'):
                logger.error(f"🚨 {engine_id}: {len(reading['alerts'])} alerts triggered")
            
            logger.debug(f"✅ Processed reading from {engine_id}, cycle {reading['cycle']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process reading: {e}")
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        logger.info(f"👂 Starting to consume from topic '{self.topic}'...")
        logger.info("🔄 Waiting for engine sensor data...")
        
        readings_processed = 0
        start_time = datetime.now()
        
        try:
            for message in self.consumer:
                reading = message.value
                self.process_reading(reading)
                
                readings_processed += 1
                
                # Log progress every 10 readings
                if readings_processed % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = readings_processed / elapsed
                    logger.info(f"📊 Processed {readings_processed} readings "
                               f"({rate:.1f} readings/sec)")
                
        except KeyboardInterrupt:
            logger.info("⏹️  Consumer stopped by user")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close consumer and database connections"""
        if self.consumer:
            self.consumer.close()
        self.db_manager.close()
        logger.info("✅ Consumer closed")

def main():
    """Main consumer application"""
    logger.info("🚀 Starting Engine Sensor Consumer...")
    
    try:
        consumer = EngineSensorConsumer()
        consumer.start_consuming()
    except Exception as e:
        logger.error(f"❌ Failed to start consumer: {e}")

if __name__ == "__main__":
    main()