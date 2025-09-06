# Aircraft Engine Monitoring System

A comprehensive, production-ready real-time aircraft engine monitoring platform for predictive maintenance, implementing modern data engineering practices with Apache Kafka, PostgreSQL, Redis, and containerized microservices architecture.

## Overview

This system provides end-to-end real-time monitoring of aircraft engine health through streaming sensor data analysis, featuring automated alerting, predictive analytics, and interactive visualization capabilities. Built on enterprise-grade technologies with full Docker containerization and CI/CD pipeline integration.

## Key Features

- **Real-time Data Streaming**: Apache Kafka-based message processing with sub-second latency
- **Multi-Engine Fleet Monitoring**: Simultaneous monitoring of multiple engine units with individual health tracking
- **Predictive Maintenance**: Remaining Useful Life (RUL) calculation and degradation pattern recognition  
- **Interactive Dashboard**: Live Streamlit-based monitoring interface with real-time fleet status
- **Automated Alerting**: Threshold-based critical parameter monitoring with configurable alerts
- **Time-Series Analytics**: Historical trend analysis with PostgreSQL and Redis caching
- **Production-Ready Infrastructure**: Complete Docker containerization with multi-environment support

## Architecture

### System Components

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Engine Data    │───▶│    Kafka     │───▶│    Consumer     │───▶│ PostgreSQL   │
│   Simulators    │    │   Producer   │    │   Processing    │    │   Database   │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                                                     │                       │
                       ┌──────────────┐             ▼                       │
                       │  Streamlit   │    ┌─────────────────┐              │
                       │  Dashboard   │◀───│     Redis       │◀─────────────┘
                       └──────────────┘    │     Cache       │
                                          └─────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Message Streaming** | Apache Kafka 7.4.0 | Real-time data ingestion and processing |
| **Database** | PostgreSQL 13 | Time-series sensor data storage with optimized indexing |
| **Caching** | Redis 6.2 | High-performance data caching and real-time analytics |
| **Coordination** | Apache Zookeeper | Kafka cluster coordination and configuration management |
| **Frontend** | Streamlit | Interactive monitoring dashboard and visualization |
| **Containerization** | Docker & Docker Compose | Microservices deployment and orchestration |
| **CI/CD** | Jenkins | Automated testing, building, and deployment pipeline |

## Quick Start

### Prerequisites

- **Docker**: Version 20.10+ with Docker Compose
- **Python**: 3.11+ for local development
- **Git**: For repository cloning
- **Minimum System Requirements**: 4GB RAM, 2 CPU cores

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/raksha-rane/Aircraft-Engine-Monitoring.git
   cd Aircraft-Engine-Monitoring
   ```

2. **Start the infrastructure services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify service health**:
   ```bash
   docker-compose ps
   ```

4. **Initialize Python environment** (for local development):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Running the System

#### Option 1: Full Docker Deployment (Recommended)
```bash
# Start all services including applications
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f producer consumer dashboard
```

#### Option 2: Hybrid Deployment (Development)
```bash
# Start infrastructure only
docker-compose up -d kafka postgres redis zookeeper

# Run applications locally
python src/kafka_producer.py    # Terminal 1
python src/kafka_consumer.py    # Terminal 2  
streamlit run src/dashboard.py  # Terminal 3
```

### Access Points

- **📊 Live Dashboard**: http://localhost:8501
- **🔍 Database**: PostgreSQL at `localhost:5433` (postgres/password)
- **⚡ Cache**: Redis at `localhost:6379`
- **📨 Message Queue**: Kafka at `localhost:9092`

## Sensor Configuration

Based on NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) specifications:

### Dataset Attribution

This system utilizes the **NASA Turbofan Engine Degradation Simulation Dataset**, a comprehensive collection of engine sensor data from the Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) program.

**Dataset Source**: [NASA Turbofan Engine Degradation Simulation](https://www.kaggle.com/datasets/bishals098/nasa-turbofan-engine-degradation-simulation)  
**Original Research**: NASA Prognostics Center of Excellence (PCoE)  
**Publication**: A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage propagation modeling for aircraft engine run-to-failure simulation," in the Proceedings of the 1st International Conference on Prognostics and Health Management (PHM08), 2008.

The dataset consists of multivariate time series data from simulated aircraft engine degradation, including:
- **4 different operating conditions** and **6 fault modes**
- **21 sensor measurements** per engine cycle
- **Train/test datasets** with known failure modes
- **Remaining Useful Life (RUL)** labels for supervised learning

### Monitored Parameters

| Category | Sensors | Description | Units |
|----------|---------|-------------|-------|
| **Temperature** | T2, T24, T30, T50, T48 | Fan inlet, LPC outlet, HPC outlet, LPT outlet, HPT outlet | °R |
| **Pressure** | P2, P21, P48, P30 | Fan inlet, HPC outlet, HPT coolant bleed, HPC outlet | psia |
| **Speed** | Nf, Nc | Physical fan speed, Physical core speed | rpm |
| **Performance** | epr, Ps30, phi, NRf, NRc, BPR, farB, htBleed, Nf_dmd, PCNfR_dmd, W31, W32 | Engine performance metrics | Various |

### Health States

- **🟢 Healthy**: Normal operation within expected parameters
- **🟡 Degrading**: Moderate wear patterns, trending toward maintenance thresholds  
- **🔴 Critical**: High degradation, immediate maintenance required

## Data Flow

### Processing Pipeline

1. **Data Generation**: Multiple engine simulators generate realistic sensor readings
2. **Stream Ingestion**: Kafka producers publish sensor data to dedicated topics
3. **Real-time Processing**: Kafka consumers process messages and apply business logic
4. **Data Persistence**: Structured storage in PostgreSQL with time-series optimization
5. **Caching**: Redis stores frequently accessed data for sub-millisecond retrieval
6. **Visualization**: Streamlit dashboard provides real-time monitoring interface

### Alert Management

- **Threshold Monitoring**: Continuous evaluation of critical sensor parameters
- **Severity Classification**: Multi-level alert system (Warning, Critical, Emergency)
- **Automated Notification**: Real-time alert generation and storage
- **Historical Tracking**: Complete audit trail of all system alerts

## Development

### Project Structure

```
aircraft-engine-monitoring/
├── src/                          # Core application code
│   ├── config.py                 # Environment-based configuration management
│   ├── kafka_producer.py         # Real-time data streaming service
│   ├── kafka_consumer.py         # Message processing and data storage
│   ├── dashboard.py              # Streamlit monitoring interface
│   ├── ml_models.py              # Machine learning models and predictions
│   ├── ml_inference.py           # Real-time ML inference service
│   ├── sensor_schema.py          # Engine sensor definitions and validation
│   ├── data_simulator.py         # Realistic engine data simulation
│   └── query_database.py         # Database inspection and query tools
├── data/                         # Dataset and analysis files
│   ├── *.txt                     # NASA C-MAPSS dataset files
│   └── analysis/                 # Generated analysis and statistics
├── notebooks/                    # Jupyter analysis notebooks
│   └── 01_data_exploration.ipynb # Comprehensive data analysis
├── models/                       # Trained ML models and artifacts
├── deployment/                   # Production deployment configurations
├── tests/                        # Comprehensive test suite
├── docker-compose.yml            # Main service orchestration
├── docker-compose.test.yml       # Testing environment
├── docker-compose.prod.yml       # Production configuration
├── Jenkinsfile                   # CI/CD pipeline definition
└── requirements.txt              # Python dependencies
```

### Environment Configuration

The system supports multiple deployment environments through configuration management:

- **Development**: Local development with debug settings
- **Staging**: Docker-based testing environment  
- **Production**: Optimized production deployment with security features

### Testing

```bash
# Run unit tests
docker-compose -f docker-compose.test.yml up --build test

# Integration testing
python -m pytest tests/ -v

# Performance testing
python tests/performance_tests.py
```

## Deployment

### Production Deployment

The system includes comprehensive production deployment support:

- **AWS ECS**: Container orchestration with auto-scaling
- **Kubernetes**: Full K8s manifests with Helm charts
- **Digital Ocean**: Droplet-based deployment with load balancing
- **Docker Swarm**: Multi-node container clustering

See `deployment/` directory for detailed deployment guides and configurations.

### CI/CD Pipeline

Jenkins-based continuous integration includes:

- **Automated Testing**: Unit, integration, and performance tests
- **Container Building**: Multi-stage Docker builds with optimization
- **Security Scanning**: Vulnerability assessment and compliance checking
- **Deployment Automation**: Environment-specific deployment with rollback capability

## Performance Metrics

### Current Capabilities

- **Throughput**: 1000+ messages/second processing capacity
- **Latency**: Sub-second end-to-end data processing
- **Storage**: Optimized time-series data with automatic partitioning
- **Availability**: 99.9% uptime with health monitoring and auto-recovery
- **Scalability**: Horizontal scaling support for increased load

### Monitoring & Observability

- **Health Checks**: Comprehensive service health monitoring
- **Metrics Collection**: Application and infrastructure metrics
- **Log Aggregation**: Centralized logging with structured output
- **Performance Dashboards**: Real-time system performance visualization

## Machine Learning Integration

### Predictive Models

- **Remaining Useful Life (RUL)**: Regression models for maintenance planning
- **Anomaly Detection**: Unsupervised learning for pattern recognition
- **Health Classification**: Multi-class classification for engine state assessment
- **Failure Prediction**: Early warning system for critical failures

### Model Management

- **Training Pipeline**: Automated model training and validation
- **Model Versioning**: MLflow integration for model lifecycle management
- **Real-time Inference**: Low-latency prediction serving
- **Performance Monitoring**: Model drift detection and retraining triggers

## Security

### Data Protection

- **Environment Variables**: Secure configuration management
- **Network Isolation**: Container network security
- **Access Control**: Role-based access with authentication
- **Data Encryption**: In-transit and at-rest encryption support

### Production Security

- **Secret Management**: External secret store integration
- **Certificate Management**: TLS/SSL configuration
- **Network Policies**: Firewall and network segmentation
- **Audit Logging**: Comprehensive security event logging

## Contributing

We welcome contributions to enhance the platform's capabilities:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- **Code Quality**: Follow PEP 8 standards with comprehensive testing
- **Documentation**: Update documentation for all new features
- **Testing**: Include unit and integration tests for new functionality
- **Performance**: Consider performance impact and optimize accordingly

## Acknowledgments

### Dataset Attribution

This project uses the **NASA Turbofan Engine Degradation Simulation Dataset** from the NASA Prognostics Center of Excellence (PCoE).

**Citation**:
```
Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). 
Damage propagation modeling for aircraft engine run-to-failure simulation. 
In Proceedings of the 1st International Conference on Prognostics and Health Management (PHM08).
```

**Data Source**: [Kaggle - NASA Turbofan Engine Degradation Simulation](https://www.kaggle.com/datasets/bishals098/nasa-turbofan-engine-degradation-simulation)

**Original Repository**: NASA Prognostics Data Repository  
**License**: NASA Open Data Policy

We acknowledge NASA's contribution to the prognostics and health management research community through the provision of this high-quality simulation dataset, which enables advancement in predictive maintenance technologies for aviation systems.

### Technology Stack

Special recognition to the open-source community and the following technologies that make this system possible:

- **Apache Kafka** - Real-time streaming platform
- **PostgreSQL** - Advanced open-source database
- **Redis** - In-memory data structure store
- **Docker** - Containerization platform
- **Streamlit** - Python web application framework
- **scikit-learn** - Machine learning library

## Support

For questions, issues, or contributions:

- **Issues**: GitHub Issues for bug reports and feature requests
- **Documentation**: Comprehensive guides in the `docs/` directory
- **Examples**: Sample configurations and use cases in `examples/`

---

**Built with ❤️ for the aviation industry** - Enabling predictive maintenance through real-time data intelligence.
