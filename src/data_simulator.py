"""
Engine Sensor Data Simulator
Generates realistic streaming sensor data based on NASA C-MAPSS patterns
"""

import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict
import pandas as pd

# Import your sensor schema
from sensor_schema import EngineSchema, SensorConfig

class EngineSimulator:
    """Simulates a single engine with realistic sensor data and degradation"""
    
    def __init__(self, engine_id: str, schema: EngineSchema, health_state: str = "healthy"):
        self.engine_id = engine_id
        self.schema = schema
        self.health_state = health_state  # "healthy", "degrading", "critical"
        self.cycle = 0
        self.start_time = datetime.now()
        
        # Initialize sensor states
        self.sensor_values = {}
        self.degradation_factors = {}
        self._initialize_sensors()
        
        # Degradation parameters
        self.degradation_rate = self._get_degradation_rate()
        self.failure_cycle = random.randint(150, 400)  # When engine will "fail"
        
    def _initialize_sensors(self):
        """Initialize sensors with baseline values"""
        for sensor_id, config in self.schema.sensors.items():
            # Start at middle of normal range
            min_val, max_val = config.normal_range
            baseline = (min_val + max_val) / 2
            self.sensor_values[sensor_id] = baseline
            self.degradation_factors[sensor_id] = 0.0  # No degradation initially
    
    def _get_degradation_rate(self) -> float:
        """Get degradation rate based on health state"""
        rates = {
            "healthy": 0.0001,     # Very slow degradation
            "degrading": 0.001,    # Moderate degradation  
            "critical": 0.005      # Fast degradation
        }
        return rates.get(self.health_state, 0.0001)
    
    def _apply_degradation(self, sensor_id: str, base_value: float) -> float:
        """Apply degradation pattern to sensor value"""
        config = self.schema.sensors[sensor_id]
        degradation = self.degradation_factors[sensor_id]
        
        if config.degradation_pattern == "increasing":
            # Temperature and some ratios increase with wear
            return base_value + (degradation * 0.1 * base_value)
        elif config.degradation_pattern == "decreasing":
            # Efficiency metrics decrease with wear
            return base_value - (degradation * 0.05 * base_value)
        elif config.degradation_pattern == "varying":
            # Speed and flow show more variation as engine degrades
            variation = degradation * 0.02 * base_value
            return base_value + random.uniform(-variation, variation)
        else:  # stable
            return base_value
    
    def _add_realistic_noise(self, sensor_id: str, value: float) -> float:
        """Add realistic sensor noise"""
        config = self.schema.sensors[sensor_id]
        if config.noise_level > 0:
            noise = np.random.normal(0, config.noise_level)
            return value + noise
        return value
    
    def _update_degradation(self):
        """Update degradation factors for all sensors"""
        progress = self.cycle / self.failure_cycle
        
        for sensor_id in self.schema.sensors:
            # Different sensors degrade at different rates
            sensor_degradation_multiplier = random.uniform(0.5, 1.5)
            self.degradation_factors[sensor_id] = (
                progress * self.degradation_rate * sensor_degradation_multiplier
            )
    
    def generate_reading(self) -> Dict:
        """Generate one complete sensor reading for current cycle"""
        self.cycle += 1
        self._update_degradation()
        
        # Generate current timestamp
        current_time = self.start_time + timedelta(seconds=self.cycle * 30)  # 30 sec intervals
        
        # Generate sensor values
        sensor_data = {}
        for sensor_id, config in self.schema.sensors.items():
            # Get base value from normal range
            min_val, max_val = config.normal_range
            if min_val == max_val:  # Constant sensors
                base_value = min_val
            else:
                # Slight variation within normal range
                base_value = random.uniform(min_val, max_val)
            
            # Apply degradation
            degraded_value = self._apply_degradation(sensor_id, base_value)
            
            # Add realistic noise
            final_value = self._add_realistic_noise(sensor_id, degraded_value)
            
            # Store with proper precision
            sensor_data[sensor_id] = round(final_value, 2)
        
        # Check if any sensors are in critical range
        alerts = self._check_alerts(sensor_data)
        
        # Complete reading
        reading = {
            "engine_id": self.engine_id,
            "timestamp": current_time.isoformat(),
            "cycle": self.cycle,
            "health_state": self._determine_health_state(sensor_data),
            "sensors": sensor_data,
            "alerts": alerts,
            "remaining_useful_life": max(0, self.failure_cycle - self.cycle)
        }
        
        return reading
    
    def _check_alerts(self, sensor_data: Dict) -> List[Dict]:
        """Check for sensor values exceeding thresholds"""
        alerts = []
        
        for sensor_id, value in sensor_data.items():
            config = self.schema.sensors[sensor_id]
            if value > config.critical_threshold:
                alerts.append({
                    "sensor": sensor_id,
                    "sensor_name": config.name,
                    "current_value": value,
                    "threshold": config.critical_threshold,
                    "severity": "critical"
                })
        
        return alerts
    
    def _determine_health_state(self, sensor_data: Dict) -> str:
        """Determine current health state based on sensor values"""
        critical_count = 0
        warning_count = 0
        
        for sensor_id, value in sensor_data.items():
            config = self.schema.sensors[sensor_id]
            min_val, max_val = config.normal_range
            
            # Check if value is approaching critical threshold
            threshold_approach = (value - max_val) / (config.critical_threshold - max_val)
            
            if threshold_approach > 0.9:
                critical_count += 1
            elif threshold_approach > 0.7:
                warning_count += 1
        
        # Determine overall health
        if critical_count > 2:
            return "critical"
        elif critical_count > 0 or warning_count > 3:
            return "degrading"
        else:
            return "healthy"


class FleetSimulator:
    """Manages multiple engine simulators"""
    
    def __init__(self, num_engines: int = 5):
        self.schema = EngineSchema()
        self.engines = []
        
        # Create fleet with different health states
        health_states = ["healthy"] * (num_engines // 2) + \
                       ["degrading"] * (num_engines // 3) + \
                       ["critical"] * (num_engines - num_engines // 2 - num_engines // 3)
        
        for i in range(num_engines):
            engine_id = f"RR_TRENT_{i+1000}"
            health = health_states[i] if i < len(health_states) else "healthy"
            self.engines.append(
                EngineSimulator(engine_id, self.schema, health)
            )
    
    def generate_fleet_reading(self) -> List[Dict]:
        """Generate readings from all engines"""
        readings = []
        for engine in self.engines:
            readings.append(engine.generate_reading())
        return readings
    
    def simulate_stream(self, duration_minutes: int = 60, interval_seconds: int = 30):
        """Simulate continuous streaming data"""
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        print(f"🚀 Starting engine simulation for {duration_minutes} minutes...")
        print(f"📊 Monitoring {len(self.engines)} engines")
        print(f"⏱️  Readings every {interval_seconds} seconds")
        print("-" * 50)
        
        while datetime.now() < end_time:
            readings = self.generate_fleet_reading()
            
            # Print summary
            healthy = sum(1 for r in readings if r["health_state"] == "healthy")
            degrading = sum(1 for r in readings if r["health_state"] == "degrading") 
            critical = sum(1 for r in readings if r["health_state"] == "critical")
            
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | "
                  f"✅ {healthy} healthy | ⚠️  {degrading} degrading | 🚨 {critical} critical")
            
            # Show alerts
            for reading in readings:
                if reading["alerts"]:
                    print(f"   🔔 {reading['engine_id']}: {len(reading['alerts'])} alerts")
            
            # In real implementation, this would send to Kafka
            # For now, we'll just yield the data
            yield readings
            
            time.sleep(interval_seconds)


# Test the simulator
if __name__ == "__main__":
    # Test single engine
    print("Testing single engine simulator...")
    schema = EngineSchema()
    engine = EngineSimulator("TEST_ENGINE_001", schema, "degrading")
    
    # Generate 5 readings
    for i in range(5):
        reading = engine.generate_reading()
        print(f"\nCycle {reading['cycle']}:")
        print(f"Health: {reading['health_state']}")
        print(f"Alerts: {len(reading['alerts'])}")
        print(f"Key sensors: T24={reading['sensors']['sensor_2']:.1f}, "
              f"T30={reading['sensors']['sensor_3']:.1f}, "
              f"Bypass_Ratio={reading['sensors']['sensor_11']:.1f}")
        time.sleep(1)
    
    print("\n" + "="*50)
    print("Testing fleet simulator...")
    
    # Test fleet simulator (just 3 iterations)
    fleet = FleetSimulator(3)
    count = 0
    for readings in fleet.simulate_stream(duration_minutes=1, interval_seconds=10):
        count += 1
        if count >= 3:  # Stop after 3 iterations for testing
            break
    
    print("✅ Simulator test completed!")