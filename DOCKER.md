# Docker Infrastructure for Aircraft Engine Monitoring

This document explains the Docker setup for the Aircraft Engine Monitoring project.

## 🐳 **Docker Architecture**

### **Service Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │    Producer     │    │    Consumer     │
│  (Streamlit)    │    │  (Data Gen)     │    │ (Data Storage)  │
│   Port: 8501    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │   PostgreSQL    │    │     Kafka       │    │     Redis       │
         │   Port: 5433    │    │   Port: 9092    │    │   Port: 6379    │
         └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 **Docker Images**

### **1. Main Application (`Dockerfile`)**
- **Purpose**: Base image for all services
- **Base**: `python:3.11-slim`
- **Features**: 
  - All Python dependencies
  - Application code
  - Health checks
  - Non-root user for security

### **2. Dashboard Service (`Dockerfile.dashboard`)**
- **Purpose**: Streamlit web dashboard
- **Port**: 8501
- **Features**: Interactive monitoring interface

### **3. Producer Service (`Dockerfile.producer`)**
- **Purpose**: Kafka data producer
- **Features**: Generates and streams sensor data

### **4. Consumer Service (`Dockerfile.consumer`)**
- **Purpose**: Kafka data consumer
- **Features**: Processes and stores sensor data

### **5. ML Training Service (`Dockerfile.ml`)**
- **Purpose**: Machine learning model training
- **Features**: 
  - Enhanced ML libraries
  - Model persistence
  - Training workflows

### **6. Test Environment (`Dockerfile.test`)**
- **Purpose**: Running tests in isolated environment
- **Features**: 
  - Testing frameworks
  - Code quality tools
  - CI/CD integration

## 🚀 **Usage Commands**

### **Development**
```bash
# Build all images
make docker-build

# Start development environment
make docker-up

# View logs
make docker-logs

# Stop environment
make docker-down
```

### **Testing**
```bash
# Run full test suite
make docker-test-run

# Start test environment only
make docker-test
```

### **Production**
```bash
# Deploy to production
make docker-prod

# With environment variables
POSTGRES_PASSWORD=secure_password make docker-prod
```

## 🌍 **Environment Management**

### **Development Environment**
- File: `docker-compose.yml`
- Features: Full application stack with development settings
- Ports: Standard ports (5433, 9092, 6379, 8501)

### **Test Environment**
- File: `docker-compose.test.yml`
- Features: Isolated testing with different ports
- Ports: Test ports (5434, 9093, 6380)
- Data: Temporary/in-memory storage

### **Production Environment**
- File: `docker-compose.prod.yml`
- Features: 
  - High availability (multiple replicas)
  - Resource limits
  - Health checks
  - SSL/TLS ready
  - Monitoring integration

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/engine_monitoring

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis
REDIS_HOST=redis

# Application
FLASK_ENV=production
PYTHONPATH=/app/src
```

### **Resource Limits (Production)**
```yaml
dashboard:
  deploy:
    replicas: 2
    resources:
      limits:
        memory: 512M
      reservations:
        memory: 256M
```

## 🚨 **Health Checks**

### **Application Health Checks**
- **Dashboard**: HTTP health endpoint
- **Producer**: Kafka connectivity test
- **Consumer**: Database/Redis connectivity
- **ML**: Library availability check

### **Infrastructure Health Checks**
- **Kafka**: Topic listing
- **PostgreSQL**: Connection test
- **Redis**: Ping command

## 🔒 **Security Features**

### **Container Security**
- Non-root user execution
- Minimal base images
- Security scanning with Trivy
- No sensitive data in images

### **Network Security**
- Isolated Docker networks
- Service-to-service communication
- No exposed internal ports

## 📊 **Monitoring**

### **Container Monitoring**
```bash
# Check container health
docker-compose ps

# View resource usage
docker stats

# Check logs
docker-compose logs -f [service]
```

### **Application Monitoring**
- Health check endpoints
- Metrics collection ready
- Log aggregation ready

## 🚀 **CI/CD Integration**

### **Jenkins Pipeline Features**
- Parallel image building
- Containerized testing
- Security scanning
- Multi-environment deployment
- Automated rollback

### **Pipeline Stages**
1. **Build**: Create all Docker images
2. **Test**: Run tests in containers
3. **Security**: Scan images for vulnerabilities
4. **Deploy**: Deploy to environments
5. **Monitor**: Health checks and validation

## 📈 **Scaling**

### **Horizontal Scaling**
```bash
# Scale specific service
docker-compose up -d --scale consumer=3

# Production scaling (automatic)
# See docker-compose.prod.yml for replica configuration
```

### **Vertical Scaling**
- Adjust resource limits in docker-compose files
- Monitor performance metrics
- Optimize based on usage patterns

## 🐛 **Troubleshooting**

### **Common Issues**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs [service]

# Restart specific service
docker-compose restart [service]

# Rebuild image
docker-compose build [service]

# Clean restart
make docker-clean && make docker-up
```

### **Debug Mode**
```bash
# Run service interactively
docker run -it aircraft-engine-app /bin/bash

# Override command
docker-compose run dashboard /bin/bash
```

## 📋 **Best Practices**

### **Image Management**
- Use multi-stage builds for optimization
- Layer caching for faster builds
- Regular security updates
- Minimal image sizes

### **Data Management**
- Named volumes for persistence
- Regular backups
- Data migration strategies
- Environment-specific data isolation

### **Performance**
- Resource monitoring
- Container optimization
- Network optimization
- Storage optimization

This Docker infrastructure provides a robust, scalable, and maintainable foundation for the Aircraft Engine Monitoring system with full CI/CD integration.
