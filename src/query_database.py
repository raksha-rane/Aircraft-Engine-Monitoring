"""
Database Query Tool for Aircraft Engine Monitoring
Quick tool to check stored sensor data and system status
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
import sys
import os

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            dbname='engine_monitoring',
            user='postgres',
            password='password'
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def query_latest_readings(conn, limit=10):
    """Get latest sensor readings"""
    query = """
    SELECT 
        engine_id,
        timestamp,
        cycle,
        health_state,
        remaining_useful_life,
        sensor_data->>'sensor_2' as temp_t24,
        sensor_data->>'sensor_3' as temp_t30,
        sensor_data->>'sensor_11' as bypass_ratio,
        created_at
    FROM sensor_readings 
    ORDER BY created_at DESC 
    LIMIT %s
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[limit])
        return df
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None

def query_fleet_status(conn):
    """Get current fleet status"""
    query = """
    SELECT 
        current_health_state,
        COUNT(*) as engine_count,
        AVG(remaining_useful_life) as avg_rul,
        SUM(active_alerts_count) as total_alerts
    FROM engine_status 
    GROUP BY current_health_state
    ORDER BY current_health_state
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"❌ Fleet status query failed: {e}")
        return None

def query_alerts(conn, limit=10):
    """Get recent alerts"""
    query = """
    SELECT 
        engine_id,
        timestamp,
        sensor_name,
        current_value,
        threshold_value,
        severity,
        created_at
    FROM alerts 
    ORDER BY created_at DESC 
    LIMIT %s
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[limit])
        return df
    except Exception as e:
        print(f"❌ Alerts query failed: {e}")
        return None

def get_database_stats(conn):
    """Get database statistics"""
    stats = {}
    
    # Count total readings
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            stats['total_readings'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts")
            stats['total_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM engine_status")
            stats['engines_tracked'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM sensor_readings")
            result = cursor.fetchone()
            stats['first_reading'] = result[0]
            stats['last_reading'] = result[1]
    except Exception as e:
        print(f"❌ Stats query failed: {e}")
        return {}
    
    return stats

def main():
    """Main function"""
    print("🔍 Aircraft Engine Monitoring - Database Query Tool")
    print("=" * 55)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    print("✅ Connected to database successfully!")
    print(f"🕒 Query time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get database statistics
    print("📊 DATABASE STATISTICS")
    print("-" * 25)
    stats = get_database_stats(conn)
    if stats:
        print(f"Total Readings: {stats.get('total_readings', 0):,}")
        print(f"Total Alerts: {stats.get('total_alerts', 0):,}")
        print(f"Engines Tracked: {stats.get('engines_tracked', 0)}")
        if stats.get('first_reading') and stats.get('last_reading'):
            print(f"Data Range: {stats['first_reading']} to {stats['last_reading']}")
    print()
    
    # Get fleet status
    print("🏭 CURRENT FLEET STATUS")
    print("-" * 25)
    fleet_status = query_fleet_status(conn)
    if fleet_status is not None and not fleet_status.empty:
        print(fleet_status.to_string(index=False))
    else:
        print("No fleet data available")
    print()
    
    # Get latest readings
    print("📋 LATEST SENSOR READINGS (Last 10)")
    print("-" * 38)
    latest_readings = query_latest_readings(conn, 10)
    if latest_readings is not None and not latest_readings.empty:
        # Format numeric columns
        if 'temp_t24' in latest_readings.columns:
            latest_readings['temp_t24'] = pd.to_numeric(latest_readings['temp_t24'], errors='coerce').round(1)
        if 'temp_t30' in latest_readings.columns:
            latest_readings['temp_t30'] = pd.to_numeric(latest_readings['temp_t30'], errors='coerce').round(1)
        if 'bypass_ratio' in latest_readings.columns:
            latest_readings['bypass_ratio'] = pd.to_numeric(latest_readings['bypass_ratio'], errors='coerce').round(2)
        
        print(latest_readings[['engine_id', 'health_state', 'cycle', 'temp_t24', 'temp_t30', 'bypass_ratio']].to_string(index=False))
    else:
        print("No sensor readings available")
    print()
    
    # Get recent alerts
    print("🚨 RECENT ALERTS (Last 10)")
    print("-" * 23)
    recent_alerts = query_alerts(conn, 10)
    if recent_alerts is not None and not recent_alerts.empty:
        print(recent_alerts[['engine_id', 'sensor_name', 'current_value', 'threshold_value', 'severity']].to_string(index=False))
    else:
        print("No alerts found")
    print()
    
    conn.close()
    print("✅ Database query completed successfully!")

if __name__ == "__main__":
    main()
