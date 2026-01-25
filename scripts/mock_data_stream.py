"""
Mock Data Stream Generator for MTI (Miami Telemetry Interface)

This script simulates sensor telemetry data by inserting random values
into the database at regular intervals. Run this as a standalone process
alongside the Flask application during development.

Usage:
    python scripts/mock_data_stream.py
"""

import os
import sys
import time
import random
from datetime import datetime

# Add the project root to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import SensorData


# Sensor configuration
SENSORS = [
    {'name': 'Arm_Servo_1', 'unit': 'deg', 'min': 0, 'max': 180},
    {'name': 'Arm_Servo_2', 'unit': 'deg', 'min': 0, 'max': 180},
    {'name': 'Motor_Temp', 'unit': 'C', 'min': 20, 'max': 85},
    {'name': 'Motor_RPM', 'unit': 'RPM', 'min': 0, 'max': 5000},
    {'name': 'Battery_Voltage', 'unit': 'V', 'min': 10, 'max': 14},
    {'name': 'System_Load', 'unit': '%', 'min': 0, 'max': 100},
]

# Interval between data points (seconds)
DATA_INTERVAL = 1.0


def get_status(value, sensor):
    """Determine status based on value thresholds."""
    range_size = sensor['max'] - sensor['min']
    normalized = (value - sensor['min']) / range_size
    
    if normalized > 0.9:
        return 'WARNING'
    elif normalized > 0.95:
        return 'ERROR'
    return 'OK'


def generate_sensor_data(sensor):
    """Generate a random sensor reading."""
    value = random.uniform(sensor['min'], sensor['max'])
    status = get_status(value, sensor)
    
    return SensorData(
        sensor_name=sensor['name'],
        value=round(value, 2),
        unit=sensor['unit'],
        status=status
    )


def main():
    """Main loop for generating mock data."""
    print("=" * 60)
    print("MTI Mock Data Stream Generator")
    print("=" * 60)
    print(f"Sensors: {len(SENSORS)}")
    print(f"Interval: {DATA_INTERVAL}s")
    print("-" * 60)
    
    # Create the Flask app context
    app = create_app('default')
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        print("Starting data generation...")
        print("Press Ctrl+C to stop.\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                timestamp = datetime.utcnow()
                
                # Generate data for each sensor
                for sensor in SENSORS:
                    data = generate_sensor_data(sensor)
                    db.session.add(data)
                
                db.session.commit()
                
                # Log progress
                print(f"[{timestamp.strftime('%H:%M:%S')}] Iteration {iteration}: "
                      f"Inserted {len(SENSORS)} readings")
                
                time.sleep(DATA_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n" + "-" * 60)
            print("Data generation stopped.")
            print(f"Total iterations: {iteration}")
            print(f"Total readings generated: {iteration * len(SENSORS)}")


if __name__ == '__main__':
    main()
