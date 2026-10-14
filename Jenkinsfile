
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'TicketSphere source code checked out.'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'py -3.12 -m pip install -r requirements.txt'
            }
        }

        stage('Automated Tests') {
            steps {
                bat 'py -3.12 -m pytest -q'
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker compose build'
            }
        }

        stage('Deploy TicketSphere') {
            steps {
                bat 'docker compose up -d'
            }
        }

        stage('Health Verification') {
            steps {
                bat 'docker compose ps'
                bat 'curl.exe --fail --silent --show-error http://localhost:8080/health'
            }
        }
    }
}

