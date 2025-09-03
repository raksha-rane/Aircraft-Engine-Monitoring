"""
Aircraft Engine Monitoring Dashboard
Real-time monitoring interface for engine sensor data
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import sys
import os
from datetime import datetime, timedelta
import json

# Add src directory to path
sys.path.append('src')

try:
    from sensor_schema import EngineSchema
    from data_simulator import FleetSimulator
    import redis
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Make sure all required packages are installed and src/ directory is accessible")

# Page configuration
st.set_page_config(
    page_title="Aircraft Engine Monitoring",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-card {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff4b4b;
    }
    .healthy-card {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00cc00;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_schema():
    """Load engine schema configuration"""
    return EngineSchema()

@st.cache_data(ttl=30)  # Cache for 30 seconds
def generate_mock_data(num_engines=5, cycles=10):
    """Generate mock streaming data"""
    schema = load_schema()
    fleet = FleetSimulator(num_engines)
    
    all_data = []
    for cycle in range(cycles):
        readings = fleet.generate_fleet_reading()
        for reading in readings:
            # Flatten the reading for easier analysis
            flat_reading = {
                'timestamp': reading['timestamp'],
                'engine_id': reading['engine_id'],
                'cycle': reading['cycle'],
                'health_state': reading['health_state'],
                'remaining_useful_life': reading['remaining_useful_life'],
                'alert_count': len(reading.get('alerts', []))
            }
            # Add sensor data
            for sensor_id, value in reading['sensors'].items():
                flat_reading[sensor_id] = value
            
            all_data.append(flat_reading)
    
    return pd.DataFrame(all_data)

def create_gauge_chart(value, title, min_val=0, max_val=100, threshold=80):
    """Create a gauge chart for KPIs"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        title = {'text': title},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, threshold], 'color': "lightgray"},
                {'range': [threshold, max_val], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))
    fig.update_layout(height=250)
    return fig

def create_sensor_trend_chart(df, sensor_ids, title):
    """Create trend charts for sensors"""
    schema = load_schema()
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, sensor_id in enumerate(sensor_ids):
        if sensor_id in df.columns:
            config = schema.sensors.get(sensor_id, None)
            sensor_name = config.name if config else sensor_id
            
            for j, engine_id in enumerate(df['engine_id'].unique()):
                engine_data = df[df['engine_id'] == engine_id].sort_values('cycle')
                
                fig.add_trace(go.Scatter(
                    x=engine_data['cycle'],
                    y=engine_data[sensor_id],
                    mode='lines+markers',
                    name=f'{engine_id} - {sensor_name}',
                    line=dict(color=colors[j % len(colors)]),
                    showlegend=(i == 0)  # Only show legend for first sensor
                ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Cycle",
        yaxis_title="Sensor Value",
        height=400
    )
    
    return fig

def main():
    """Main dashboard function"""
    
    # Title and header
    st.title("✈️ Aircraft Engine Monitoring Dashboard")
    st.markdown("Real-time monitoring and analysis of aircraft engine sensor data")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Simulation controls
    num_engines = st.sidebar.slider("Number of Engines", 1, 10, 5)
    cycles_to_show = st.sidebar.slider("Cycles to Display", 5, 50, 20)
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner("Loading engine data..."):
        df = generate_mock_data(num_engines, cycles_to_show)
    
    if df.empty:
        st.error("No data available")
        return
    
    # Fleet Overview Section
    st.header("🏭 Fleet Overview")
    
    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    
    latest_data = df.groupby('engine_id').last().reset_index()
    
    with col1:
        healthy_count = len(latest_data[latest_data['health_state'] == 'healthy'])
        st.markdown(f"""
        <div class="healthy-card">
            <h3>✅ Healthy Engines</h3>
            <h2>{healthy_count}/{len(latest_data)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        degrading_count = len(latest_data[latest_data['health_state'] == 'degrading'])
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚠️ Degrading Engines</h3>
            <h2>{degrading_count}/{len(latest_data)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        critical_count = len(latest_data[latest_data['health_state'] == 'critical'])
        st.markdown(f"""
        <div class="alert-card">
            <h3>🚨 Critical Engines</h3>
            <h2>{critical_count}/{len(latest_data)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_alerts = latest_data['alert_count'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔔 Active Alerts</h3>
            <h2>{total_alerts}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Fleet health distribution
    col1, col2 = st.columns(2)
    
    with col1:
        health_dist = latest_data['health_state'].value_counts()
        fig_pie = px.pie(values=health_dist.values, names=health_dist.index,
                        title="Fleet Health Distribution",
                        color_discrete_map={
                            'healthy': 'green',
                            'degrading': 'orange', 
                            'critical': 'red'
                        })
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        avg_rul = latest_data.groupby('health_state')['remaining_useful_life'].mean()
        fig_bar = px.bar(x=avg_rul.index, y=avg_rul.values,
                        title="Average Remaining Useful Life by Health State",
                        color=avg_rul.index,
                        color_discrete_map={
                            'healthy': 'green',
                            'degrading': 'orange',
                            'critical': 'red'
                        })
        fig_bar.update_layout(yaxis_title="Remaining Useful Life (cycles)")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Engine Details Section
    st.header("🔧 Engine Sensor Analysis")
    
    # Engine selector
    selected_engines = st.multiselect(
        "Select Engines to Monitor",
        options=df['engine_id'].unique(),
        default=df['engine_id'].unique()[:3]
    )
    
    if selected_engines:
        filtered_df = df[df['engine_id'].isin(selected_engines)]
        
        # Key sensor trends
        key_sensors = ['sensor_2', 'sensor_3', 'sensor_4', 'sensor_11']  # T24, T30, T50, Bypass Ratio
        sensor_names = {
            'sensor_2': 'Temperature T24',
            'sensor_3': 'Temperature T30', 
            'sensor_4': 'Temperature T50',
            'sensor_11': 'Bypass Ratio'
        }
        
        # Create tabs for different sensor groups
        tab1, tab2, tab3 = st.tabs(["🌡️ Temperature Sensors", "📈 Performance Metrics", "🚨 Alert Analysis"])
        
        with tab1:
            temp_sensors = ['sensor_2', 'sensor_3', 'sensor_4']
            fig_temp = create_sensor_trend_chart(filtered_df, temp_sensors, "Temperature Sensor Trends")
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with tab2:
            perf_sensors = ['sensor_11', 'sensor_9', 'sensor_14']  # Bypass ratio, Core speeds
            fig_perf = create_sensor_trend_chart(filtered_df, perf_sensors, "Performance Metrics")
            st.plotly_chart(fig_perf, use_container_width=True)
        
        with tab3:
            # Alert timeline
            alert_timeline = filtered_df.groupby(['cycle', 'engine_id'])['alert_count'].sum().reset_index()
            fig_alerts = px.line(alert_timeline, x='cycle', y='alert_count', color='engine_id',
                               title="Alert Count Over Time")
            st.plotly_chart(fig_alerts, use_container_width=True)
    
    # Individual Engine Status
    st.header("📊 Individual Engine Status")
    
    # Create expandable sections for each engine
    for engine_id in latest_data['engine_id'].unique():
        engine_data = latest_data[latest_data['engine_id'] == engine_id].iloc[0]
        
        with st.expander(f"🔧 {engine_id} - {engine_data['health_state'].title()}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Health State", engine_data['health_state'].title())
                st.metric("Current Cycle", int(engine_data['cycle']))
            
            with col2:
                st.metric("Remaining Useful Life", f"{int(engine_data['remaining_useful_life'])} cycles")
                st.metric("Active Alerts", int(engine_data['alert_count']))
            
            with col3:
                # Key sensor values
                st.metric("Temp T30 (°R)", f"{engine_data.get('sensor_3', 0):.1f}")
                st.metric("Bypass Ratio", f"{engine_data.get('sensor_11', 0):.2f}")
    
    # Data table
    st.header("📋 Recent Readings")
    
    # Show latest readings for selected engines
    if selected_engines:
        recent_data = df[df['engine_id'].isin(selected_engines)].groupby('engine_id').last().reset_index()
        display_columns = ['engine_id', 'health_state', 'cycle', 'remaining_useful_life', 'alert_count']
        st.dataframe(recent_data[display_columns], use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Dashboard Features:**")
    st.markdown("• Real-time fleet health monitoring • Sensor trend analysis • Alert tracking • Predictive maintenance insights")
    
    # Refresh timestamp
    st.markdown(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
