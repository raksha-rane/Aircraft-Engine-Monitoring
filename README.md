# Aircraft Engine Monitoring ✈️

A comprehensive real-time aircraft engine monitoring system for predictive maintenance, built with Kafka, PostgreSQL, Redis, and advanced analytics.

## 🎯 **Project Status: FULLY OPERATIONAL** ✅

- **Real-time streaming**: Engine sensor data flowing through Kafka
- **Data storage**: PostgreSQL with 100+ readings, Redis caching
- **Live monitoring**: Interactive Streamlit dashboard
- **Alert system**: Critical threshold monitoring active
- **Analytics**: Jupyter notebooks with sensor pattern analysis

## 🏗️ **Architecture**

This project implements a modern data engineering pipeline with microservices architecture:

### **Core Components:**
- **Apache Kafka**: Real-time message streaming platform (localhost:9092)
- **PostgreSQL**: Time-series sensor data storage (localhost:5433)
- **Redis**: High-speed caching and real-time analytics (localhost:6379)
- **Apache Zookeeper**: Kafka coordination service
- **Streamlit**: Interactive monitoring dashboard (localhost:8501)

### **Data Flow:**
```
Engine Simulators → Kafka Producer → Kafka Topic → Kafka Consumer → PostgreSQL + Redis
                                                        ↓
                               Streamlit Dashboard ← Analytics & Alerts
```

## 🚀 **Quick Start**

### Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ (virtual environment recommended)

### 🏃‍♂️ **Running the Complete System**

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd aircraft-engine-monitoring
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start infrastructure services**:
   ```bash
   docker-compose up -d
   ```

3. **Start the streaming pipeline** (separate terminals):
   ```bash
   # Terminal 1: Start producer
   python src/kafka_producer.py
   
   # Terminal 2: Start consumer  
   python src/kafka_consumer.py
   
   # Terminal 3: Launch dashboard
   streamlit run src/dashboard.py
   ```

4. **Access monitoring interfaces**:
   - **📊 Live Dashboard**: http://localhost:8501
   - **🔍 Database Query**: `python src/query_database.py`
   - **📓 Data Analysis**: Open `notebooks/01_data_exploration.ipynb`

### 🔧 **Service Endpoints**
- **Kafka**: `localhost:9092`
- **PostgreSQL**: `localhost:5433` (username: `postgres`, password: `password`)
- **Redis**: `localhost:6379`
- **Streamlit Dashboard**: `localhost:8501`

## 📊 **Current Capabilities**

### **✅ Real-time Monitoring**
- **21 engine sensors** based on NASA C-MAPSS dataset patterns
- **Multiple health states**: healthy, degrading, critical
- **Live sensor streaming** with 10-second intervals
- **Threshold-based alerting** for critical parameters

### **✅ Data Management**
- **Time-series storage** in PostgreSQL with optimized indexes
- **Real-time caching** in Redis for fast access
- **Alert tracking** and management
- **Fleet status** monitoring and reporting

### **✅ Analytics & Visualization** 
- **Interactive dashboard** with real-time fleet overview
- **Sensor trend analysis** with temperature, pressure, speed metrics
- **Health state visualization** and RUL tracking
- **Jupyter notebooks** for deep data exploration

### **✅ Predictive Maintenance Foundation**
- **Remaining Useful Life (RUL)** calculation
- **Degradation pattern** recognition
- **Early warning system** through sensor correlation
- **Alert management** for maintenance scheduling

## 📁 **Project Structure**

```
aircraft-engine-monitoring/
├── 🐳 docker-compose.yml         # Infrastructure services
├── 📊 STATUS.md                  # Current system status
├── 📚 data/                      # NASA C-MAPSS dataset and analysis
│   ├── *.txt                     # Original NASA dataset files  
│   └── analysis/                 # Generated analysis results
├── 📓 notebooks/                 # Jupyter analysis notebooks
│   └── 01_data_exploration.ipynb # Comprehensive data analysis
├── 🔧 src/                       # Core application code
│   ├── sensor_schema.py          # Engine sensor definitions (21 sensors)
│   ├── data_simulator.py         # Realistic engine data simulation
│   ├── kafka_producer.py         # Real-time data streaming
│   ├── kafka_consumer.py         # Data processing and storage
│   ├── dashboard.py              # Streamlit monitoring interface
│   ├── query_database.py         # Database inspection tool
│   └── explore_data.py           # Data exploration utilities
└── 📋 README.md                  # This file
```

## 🔬 **Technical Details**

### **Sensor Configuration**
Based on NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS):

- **🌡️ Temperature Sensors (5)**: T2, T24, T30, T50, T48 (°R)
- **📈 Pressure Sensors (4)**: P2, P21, P48, P30 (psia)  
- **⚡ Speed Sensors (4)**: Physical/Corrected Fan & Core speeds (RPM)
- **📊 Performance Metrics (8)**: Bypass ratio, fuel flow, enthalpies, etc.

### **Health States & Degradation**
- **Healthy**: Normal operation, minimal sensor drift
- **Degrading**: Moderate wear, increasing sensor values
- **Critical**: High degradation, frequent alert triggers

### **Alert System**
- **Temperature thresholds**: T24 (645°R), T30 (1620°R), T50 (1445°R)
- **Real-time monitoring**: Continuous threshold checking
- **Severity levels**: Critical alerts stored and tracked
- **Maintenance triggers**: Automated alert generation

## 🚀 **Development Roadmap**

### **🔥 Phase 1: Complete Foundation** ✅
- [x] Docker infrastructure setup
- [x] Kafka streaming pipeline  
- [x] PostgreSQL data storage
- [x] Redis caching layer
- [x] Streamlit dashboard
- [x] Alert system implementation

### **🤖 Phase 2: Machine Learning (In Progress)**
- [ ] RUL prediction models
- [ ] Anomaly detection algorithms  
- [ ] Health state classification
- [ ] Failure mode pattern recognition

### **📈 Phase 3: Advanced Analytics**
- [ ] Time-series forecasting
- [ ] Maintenance optimization
- [ ] Cost-benefit analysis
- [ ] Fleet comparison tools

### **🏭 Phase 4: Production Readiness**
- [ ] API development
- [ ] Kubernetes deployment
- [ ] Performance optimization
- [ ] Security implementation

## 📋 **Current Data Metrics**
- **Total Readings**: 100+ sensor measurements stored
- **Active Alerts**: 8 critical temperature alerts
- **Fleet Status**: 3 healthy, 1 degrading engine
- **Data Rate**: 18 readings/minute (3 engines × 6 readings/minute)
- **Storage**: PostgreSQL + Redis with optimized indexing

## 💡 **Key Features Demonstrated**

✅ **End-to-end streaming**: From simulation to visualization  
✅ **Real-time processing**: Sub-second latency  
✅ **Scalable architecture**: Microservices with message queues  
✅ **Time-series analytics**: Historical trend analysis  
✅ **Interactive monitoring**: Live dashboard with fleet overview  
✅ **Predictive insights**: RUL tracking and health classification  

---

## 🤝 **Contributing**

This project showcases modern data engineering practices for industrial IoT and predictive maintenance. Areas for contribution:

- **Machine Learning**: RUL prediction and anomaly detection models
- **Visualization**: Enhanced dashboard features and charts  
- **Optimization**: Performance tuning and scalability improvements
- **Integration**: External system APIs and data sources

## 📄 **License**

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🚁 **System Status**: All components operational and streaming live data!
