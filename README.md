# Aircraft Engine Monitoring

A real-time aircraft engine monitoring system built with Kafka, PostgreSQL, and Redis.

## Architecture

This project uses a microservices architecture with the following components:

- **Apache Kafka**: Message streaming platform for real-time data ingestion
- **PostgreSQL**: Primary database for storing engine monitoring data
- **Redis**: In-memory data store for caching and real-time analytics
- **Apache Zookeeper**: Coordination service for Kafka

## Quick Start

### Prerequisites

- Docker and Docker Compose installed on your system

### Running the System

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd aircraft-engine-monitoring
   ```

2. Start all services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Verify services are running:
   ```bash
   docker-compose ps
   ```

### Services

- **Kafka**: Available at `localhost:9092`
- **PostgreSQL**: Available at `localhost:5432`
  - Database: `engine_monitoring`
  - Username: `postgres`
  - Password: `password`
- **Redis**: Available at `localhost:6379`

## Project Structure

```
aircraft-engine-monitoring/
├── docker-compose.yml      # Docker services configuration
├── data/                   # Data storage directory
├── notebooks/              # Jupyter notebooks for analysis
├── src/                    # Source code
└── README.md              # This file
```

## Development

More documentation and development guidelines will be added as the project evolves.

## License

This project is licensed under the MIT License.
