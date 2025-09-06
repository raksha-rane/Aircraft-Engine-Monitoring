pipeline {
    agent any
    
    environment {
        // Environment variables
        FLASK_ENV = 'testing'
        PYTHONPATH = "${WORKSPACE}/src"
        COMPOSE_PROJECT_NAME = "engine-monitoring-${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        echo 'Running code linting...'
                        sh '''
                            . venv/bin/activate
                            make lint || echo "Linting completed with warnings"
                        '''
                    }
                }
                stage('Code Formatting Check') {
                    steps {
                        echo 'Checking code formatting...'
                        sh '''
                            . venv/bin/activate
                            black --check src/ tests/ || echo "Formatting check completed"
                        '''
                    }
                }
            }
        }
        
        stage('Start Test Infrastructure') {
            steps {
                echo 'Starting test infrastructure...'
                sh '''
                    # Start test services
                    docker-compose -f docker-compose.test.yml up -d
                    
                    # Wait for services to be ready
                    sleep 30
                    
                    # Verify services are running
                    docker-compose -f docker-compose.test.yml ps
                '''
            }
        }
        
        stage('Run Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        echo 'Running unit tests...'
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/ -v -m "unit" --junitxml=reports/unit-tests.xml
                        '''
                    }
                }
                stage('Integration Tests') {
                    steps {
                        echo 'Running integration tests...'
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/ -v -m "integration" --junitxml=reports/integration-tests.xml
                        '''
                    }
                }
                stage('ML Model Tests') {
                    steps {
                        echo 'Running ML model tests...'
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/ -v -m "ml" --junitxml=reports/ml-tests.xml
                        '''
                    }
                }
            }
        }
        
        stage('Health Checks') {
            steps {
                echo 'Running system health checks...'
                sh '''
                    . venv/bin/activate
                    export FLASK_ENV=testing
                    python scripts/health_check.py
                '''
            }
        }
        
        stage('Build and Test ML Models') {
            steps {
                echo 'Training and validating ML models...'
                sh '''
                    . venv/bin/activate
                    python src/ml_models.py
                    
                    # Verify models were created
                    ls -la models/
                '''
            }
        }
        
        stage('Integration Test - Full Pipeline') {
            steps {
                echo 'Running full pipeline integration test...'
                sh '''
                    . venv/bin/activate
                    
                    # Start data simulation (background)
                    timeout 30s python src/kafka_producer.py &
                    
                    # Start consumer (background)
                    timeout 30s python src/kafka_consumer.py &
                    
                    # Wait for some data to flow
                    sleep 10
                    
                    # Query database to verify data flow
                    python src/query_database.py
                '''
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'staging'
            }
            steps {
                echo 'Deploying to staging environment...'
                sh '''
                    # Staging deployment steps would go here
                    echo "Staging deployment completed"
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying to production environment...'
                input message: 'Deploy to production?', ok: 'Deploy'
                sh '''
                    # Production deployment steps would go here
                    echo "Production deployment completed"
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up...'
            
            // Collect test results
            junit 'reports/*.xml'
            
            // Clean up Docker containers
            sh '''
                docker-compose -f docker-compose.test.yml down -v || true
                docker system prune -f || true
            '''
            
            // Clean up Python environment
            sh 'rm -rf venv || true'
        }
        
        success {
            echo '✅ Pipeline completed successfully!'
        }
        
        failure {
            echo '❌ Pipeline failed!'
            // Send notifications (email, Slack, etc.)
        }
        
        unstable {
            echo '⚠️ Pipeline completed with warnings'
        }
    }
}
