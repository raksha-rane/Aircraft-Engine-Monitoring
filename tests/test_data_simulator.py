"""
Unit tests for data simulator functionality
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_simulator import EngineSimulator, FleetSimulator
from sensor_schema import EngineSchema

class TestEngineSimulator:
    def setup_method(self):
        """Setup test fixtures"""
        self.schema = EngineSchema()
        self.engine = EngineSimulator("TEST_ENGINE_001", self.schema, "healthy")
    
    def test_engine_initialization(self):
        """Test engine simulator initialization"""
        assert self.engine.engine_id == "TEST_ENGINE_001"
        assert self.engine.health_state == "healthy"
        assert self.engine.cycle == 0
    
    def test_generate_reading(self):
        """Test sensor reading generation"""
        reading = self.engine.generate_reading()
        
        # Check basic structure
        assert "engine_id" in reading
        assert "timestamp" in reading
        assert "cycle" in reading
        assert "sensors" in reading
        assert "health_state" in reading
        
        # Check sensor count
        assert len(reading["sensors"]) == 21  # NASA C-MAPSS sensors
        
        # Check cycle increment
        assert reading["cycle"] == 1
    
    def test_health_state_transitions(self):
        """Test health state degradation"""
        degrading_engine = EngineSimulator("TEST_DEGRADING", self.schema, "degrading")
        
        # Generate multiple readings to test degradation
        for _ in range(10):
            reading = degrading_engine.generate_reading()
            assert reading["health_state"] in ["healthy", "degrading", "critical"]

class TestFleetSimulator:
    def setup_method(self):
        """Setup test fixtures"""
        self.fleet = FleetSimulator(num_engines=3)
    
    def test_fleet_initialization(self):
        """Test fleet simulator initialization"""
        assert len(self.fleet.engines) == 3
        assert all(engine.engine_id.startswith("ENGINE_") for engine in self.fleet.engines)
    
    def test_fleet_reading_generation(self):
        """Test fleet reading generation"""
        readings = self.fleet.generate_fleet_reading()
        
        assert len(readings) == 3
        assert all("engine_id" in reading for reading in readings)
        assert all("sensors" in reading for reading in readings)

class TestSensorSchema:
    def setup_method(self):
        """Setup test fixtures"""
        self.schema = EngineSchema()
    
    def test_sensor_configuration(self):
        """Test sensor configuration"""
        config = self.schema.get_sensor_config()
        
        # Check we have 21 sensors (NASA C-MAPSS standard)
        assert len(config.sensors) == 21
        
        # Check required sensors exist
        required_sensors = ['sensor_2', 'sensor_3', 'sensor_11']  # T24, T30, Bypass Ratio
        for sensor in required_sensors:
            assert sensor in config.sensors
    
    def test_health_state_validation(self):
        """Test health state validation"""
        valid_states = ["healthy", "degrading", "critical"]
        
        for state in valid_states:
            engine = EngineSimulator("TEST", self.schema, state)
            assert engine.health_state == state
