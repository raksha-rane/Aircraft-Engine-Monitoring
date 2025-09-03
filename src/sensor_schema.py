"""
Aircraft Engine Sensor Schema
Based on NASA C-MAPSS dataset analysis
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import random
import numpy as np

@dataclass
class SensorConfig:
    """Configuration for each sensor type"""
    name: str
    unit: str
    normal_range: Tuple[float, float]  # (min, max) for healthy operation
    degradation_pattern: str  # 'increasing', 'decreasing', 'stable', 'varying'
    noise_level: float  # Standard deviation for realistic noise
    critical_threshold: float  # Value that indicates potential failure

class EngineSchema:
    """Complete engine sensor schema based on NASA C-MAPSS data"""
    
    def __init__(self):
        self.sensors = {
            # Temperature Sensors (°R - Rankine scale)
            'sensor_1': SensorConfig(
                name='Total_Temperature_T2',
                unit='°R',
                normal_range=(518.67, 518.67),  # Constant in dataset
                degradation_pattern='stable',
                noise_level=0.0,
                critical_threshold=520.0
            ),
            'sensor_2': SensorConfig(
                name='Total_Temperature_T24',
                unit='°R', 
                normal_range=(641.21, 644.53),
                degradation_pattern='increasing',  # Increases with degradation
                noise_level=0.5,
                critical_threshold=645.0
            ),
            'sensor_3': SensorConfig(
                name='Total_Temperature_T30',
                unit='°R',
                normal_range=(1571.04, 1616.91),
                degradation_pattern='increasing',
                noise_level=5.0,
                critical_threshold=1620.0
            ),
            'sensor_4': SensorConfig(
                name='Total_Temperature_T50',
                unit='°R',
                normal_range=(1382.25, 1441.49),
                degradation_pattern='increasing',
                noise_level=8.0,
                critical_threshold=1445.0
            ),
            'sensor_7': SensorConfig(
                name='Total_Temperature_T48',
                unit='°R',
                normal_range=(549.85, 556.06),
                degradation_pattern='increasing',
                noise_level=1.0,
                critical_threshold=558.0
            ),
            'sensor_12': SensorConfig(
                name='Static_Temperature_T48',
                unit='°R',
                normal_range=(518.69, 523.38),
                degradation_pattern='increasing',
                noise_level=0.8,
                critical_threshold=525.0
            ),
            
            # Pressure Sensors (psia)
            'sensor_5': SensorConfig(
                name='Pressure_P2',
                unit='psia',
                normal_range=(14.62, 14.62),  # Constant
                degradation_pattern='stable',
                noise_level=0.0,
                critical_threshold=15.0
            ),
            'sensor_6': SensorConfig(
                name='Pressure_P21',
                unit='psia',
                normal_range=(21.60, 21.61),
                degradation_pattern='stable',
                noise_level=0.01,
                critical_threshold=22.0
            ),
            'sensor_10': SensorConfig(
                name='Pressure_P48',
                unit='psia',
                normal_range=(1.30, 1.30),  # Constant
                degradation_pattern='stable',
                noise_level=0.0,
                critical_threshold=1.35
            ),
            'sensor_16': SensorConfig(
                name='Pressure_P30',
                unit='psia',
                normal_range=(0.03, 0.03),  # Constant
                degradation_pattern='stable',
                noise_level=0.0,
                critical_threshold=0.035
            ),
            
            # Speed Sensors (RPM)
            'sensor_8': SensorConfig(
                name='Physical_Fan_Speed',
                unit='rpm',
                normal_range=(2387.90, 2388.56),
                degradation_pattern='varying',
                noise_level=0.2,
                critical_threshold=2390.0
            ),
            'sensor_9': SensorConfig(
                name='Physical_Core_Speed', 
                unit='rpm',
                normal_range=(9021.73, 9244.59),
                degradation_pattern='varying',
                noise_level=20.0,
                critical_threshold=9300.0
            ),
            'sensor_13': SensorConfig(
                name='Corrected_Fan_Speed',
                unit='rpm',
                normal_range=(2387.88, 2388.56),
                degradation_pattern='varying',
                noise_level=0.2,
                critical_threshold=2390.0
            ),
            'sensor_14': SensorConfig(
                name='Corrected_Core_Speed',
                unit='rpm', 
                normal_range=(8099.94, 8293.72),
                degradation_pattern='varying',
                noise_level=15.0,
                critical_threshold=8350.0
            ),
            
            # Ratio and Flow Sensors
            'sensor_11': SensorConfig(
                name='Bypass_Ratio',
                unit='ratio',
                normal_range=(46.85, 48.53),
                degradation_pattern='increasing',  # Notable degradation pattern
                noise_level=0.3,
                critical_threshold=49.0
            ),
            'sensor_15': SensorConfig(
                name='Burner_Fuel_Air_Ratio',
                unit='ratio',
                normal_range=(8.32, 8.58),
                degradation_pattern='varying',
                noise_level=0.05,
                critical_threshold=8.7
            ),
            'sensor_17': SensorConfig(
                name='Bleed_Enthalpy',
                unit='enthalpy',
                normal_range=(388.00, 400.00),
                degradation_pattern='varying',
                noise_level=2.0,
                critical_threshold=405.0
            ),
            'sensor_20': SensorConfig(
                name='Demanded_Fan_Speed',
                unit='rpm',
                normal_range=(38.14, 39.43),
                degradation_pattern='varying',
                noise_level=0.2,
                critical_threshold=40.0
            ),
            'sensor_21': SensorConfig(
                name='Demanded_Core_Speed', 
                unit='rpm',
                normal_range=(22.89, 23.62),
                degradation_pattern='varying',
                noise_level=0.1,
                critical_threshold=24.0
            ),
            
            # Constant/Control Sensors
            'sensor_18': SensorConfig(
                name='Static_Pressure_HPC',
                unit='psia',
                normal_range=(2388.00, 2388.00),  # Constant
                degradation_pattern='stable',
                noise_level=0.0,
                critical_threshold=2390.0
            ),
            'sensor_19': SensorConfig(
                name='Fuel_Flow_PS30',
                unit='pps',
                normal_range=(100.00, 100.00),  # Constant
                degradation_pattern='stable', 
                noise_level=0.0,
                critical_threshold=102.0
            )
        }
    
    def get_sensor_list(self):
        """Return list of all sensor names"""
        return list(self.sensors.keys())
    
    def get_degrading_sensors(self):
        """Return sensors that show degradation patterns"""
        return [name for name, config in self.sensors.items() 
                if config.degradation_pattern in ['increasing', 'decreasing']]
    
    def get_critical_sensors(self):
        """Return most important sensors for monitoring"""
        # Based on analysis, these show the most variation and degradation
        return ['sensor_2', 'sensor_3', 'sensor_4', 'sensor_11', 'sensor_9', 'sensor_14']

# Usage example
if __name__ == "__main__":
    schema = EngineSchema()
    print("Engine Sensors:")
    for sensor_id, config in schema.sensors.items():
        print(f"{sensor_id}: {config.name} ({config.unit})")
    
    print(f"\nDegrading sensors: {schema.get_degrading_sensors()}")
    print(f"Critical sensors for monitoring: {schema.get_critical_sensors()}")