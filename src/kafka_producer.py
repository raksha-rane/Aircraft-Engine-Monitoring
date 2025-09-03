"""
Kafka Producer for Engine Sensor Data
Streams real-time sensor data from engine simulator to Kafka
"""

import json
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

# Import your simulator
from data_simulator import FleetSimulator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EngineSensorProducer:
    """Kafka producer for streaming engine sensor data"""
    
    def __init__(self, bootstrap_servers=['localhost:9092'], topic='engine-sensors'):
        self.topic = topic
        self.producer = None
        self.bootstrap_servers = bootstrap_servers
        self._connect_to_kafka()
    
    def _connect_to_kafka(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8'),
                    # Configuration for reliability
                    acks='all',  # Wait for all replicas
                    retries=3,
                    batch_size=16384,
                    linger_ms=10,
                    buffer_memory=33554432
                )
                logger.info("✅ Connected to Kafka successfully")
                return
            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt + 1}: Failed to connect to Kafka: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error("❌ Failed to connect to Kafka after all retries")
                    raise
    
    def send_reading(self, reading: dict) -> bool:
        """Send a single engine reading to Kafka"""
        try:
            # Use engine_id as the key for partitioning
            key = reading['engine_id']
            
            # Send to Kafka
            future = self.producer.send(
                self.topic,
                key=key,
                value=reading
            )
            
            # Wait for confirmation (optional - makes it synchronous)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"📤 Sent reading from {key} to topic {record_metadata.topic} "
                        f"partition {record_metadata.partition} offset {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"❌ Failed to send reading for {reading.get('engine_id', 'unknown')}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending reading: {e}")
            return False
    
    def stream_fleet_data(self, num_engines=5, duration_minutes=60, interval_seconds=30):
        """Stream data from multiple engines continuously"""
        logger.info(f"🚀 Starting to stream data from {num_engines} engines")
        logger.info(f"📊 Duration: {duration_minutes} minutes, Interval: {interval_seconds} seconds")
        
        # Initialize fleet simulator
        fleet = FleetSimulator(num_engines)
        
        readings_sent = 0
        errors = 0
        start_time = datetime.now()
        
        try:
            for readings_batch in fleet.simulate_stream(duration_minutes, interval_seconds):
                batch_success = 0
                
                for reading in readings_batch:
                    if self.send_reading(reading):
                        batch_success += 1
                        readings_sent += 1
                    else:
                        errors += 1
                
                # Log batch summary
                alerts_count = sum(len(r.get('alerts', [])) for r in readings_batch)
                logger.info(f"📤 Batch sent: {batch_success}/{len(readings_batch)} readings, "
                           f"🔔 {alerts_count} alerts detected")
                
                # Show health summary
                health_summary = {}
                for reading in readings_batch:
                    health = reading['health_state']
                    health_summary[health] = health_summary.get(health, 0) + 1
                
                health_str = " | ".join([f"{state}: {count}" for state, count in health_summary.items()])
                logger.info(f"🏥 Fleet health: {health_str}")
        
        except KeyboardInterrupt:
            logger.info("⏹️  Streaming stopped by user")
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
        finally:
            # Final statistics
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"📈 Final stats: {readings_sent} readings sent, {errors} errors in {elapsed:.1f}s")
            self.close()
    
    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            self.producer.flush()  # Ensure all messages are sent
            self.producer.close()
            logger.info("✅ Kafka producer closed")

def test_connection():
    """Test basic Kafka connectivity"""
    logger.info("🧪 Testing Kafka connection...")
    
    try:
        producer = EngineSensorProducer()
        
        # Send test message
        test_reading = {
            "engine_id": "TEST_ENGINE",
            "timestamp": datetime.now().isoformat(),
            "cycle": 1,
            "health_state": "healthy",
            "sensors": {"sensor_1": 518.67, "sensor_2": 642.0},
            "alerts": [],
            "remaining_useful_life": 200
        }
        
        success = producer.send_reading(test_reading)
        
        if success:
            logger.info("✅ Kafka connection test PASSED")
        else:
            logger.error("❌ Kafka connection test FAILED")
        
        producer.close()
        return success
        
    except Exception as e:
        logger.error(f"❌ Connection test error: {e}")
        return False

if __name__ == "__main__":
    # Test connection first
    if test_connection():
        logger.info("🚀 Starting live engine sensor streaming...")
        
        # Start streaming with small fleet for testing
        producer = EngineSensorProducer()
        producer.stream_fleet_data(
            num_engines=3,           # Start with 3 engines
            duration_minutes=5,      # Run for 5 minutes
            interval_seconds=10      # Reading every 10 seconds
        )
    else:
        logger.error("❌ Cannot start streaming - Kafka connection failed")