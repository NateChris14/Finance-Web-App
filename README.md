[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Coverage](https://codecov.io/gh/NateChris14/Finance-Web-App/branch/main/graph/badge.svg)](https://codecov.io/gh/NateChris14/Finance-Web-App)
[![Last Commit](https://img.shields.io/github/last-commit/NateChris14/Finance-Web-App.svg)](https://github.com/NateChris14/Finance-Web-App/commits/main)

# Finance Web App

A full-stack finance web application that **consumes data produced by the Stock Anomaly ETL pipeline** (Airflow) and reads from a PostgreSQL database hosted on AWS RDS to power stock analysis, clustering, and interactive visualization.

## 🎬 Project Demo

Watch a quick demo of the Stock Intelligence Dashboard in action:


![Example view 1](https://github.com/NateChris14/Finance-Web-App/blob/main/Screenshot%20(806).png)


![Example view 2](https://github.com/NateChris14/Finance-Web-App/blob/main/Screenshot%20(807).png)


![Example view 3](https://github.com/NateChris14/Finance-Web-App/blob/main/Screenshot%20(808).png)

Alternatively, you can view the demo here: [Project Demo Video](https://www.youtube.com/watch?v=iKAZkYRPa68)

## Features
- **Stock Clustering:** Machine learning-based clustering of stocks using custom pipelines.
- **Interactive Visualizations:** Frontend charts and dashboards for financial data exploration.
- **REST API:** Backend API for predictions, data retrieval, and cluster analysis.
- **Dockerized Deployment:** Easy setup and deployment using Docker and Docker Compose.
- **Experiment Tracking:** MLflow integration for tracking experiments and model artifacts.
- **Testing Suite:** Automated tests for both backend and frontend components.

## Architecture
This application is designed to sit on top of an upstream ETL pipeline that loads market + macro data into PostgreSQL on AWS RDS, then serves it through a containerized backend API and a frontend dashboard deployed on AWS.

![Deployment Architecture](https://github.com/NateChris14/Finance-Web-App/blob/main/Deployment%20Architecture%20(Stock).png)

### Key components
- **Upstream ETL (Astronomer/Airflow):** Loads stock prices, technical indicators, and macro indicators into PostgreSQL (AWS RDS).
- **AWS RDS (PostgreSQL):** Primary database used by the web app backend.
- **Backend API (Flask):** Reads from PostgreSQL and exposes REST endpoints consumed by the frontend.
- **Frontend (HTML/CSS/JS):** Dashboard UI that calls the backend API.
- **CI/CD (GitHub Actions):** Builds/tests and pushes Docker images.
- **Amazon ECR:** Stores backend and frontend Docker images.
- **Amazon ECS (Fargate):** Runs the containers as tasks/services.

## Data dependency (ETL → DB → App)
This project expects the database to already contain curated tables produced by the **Stock Anomaly ETL** project.

Before running this app, ensure:
- The ETL pipeline has successfully populated your AWS RDS PostgreSQL instance.
- You know which schema/table names the backend queries (document them below once finalized).

### Expected inputs
- Upstream ETL repo: `https://github.com/NateChris14/FinanceApp`
- Database: AWS RDS PostgreSQL
- Schema/tables used by this app:
  - `stock_data` (e.g., daily prices)
  - `technical_indicators` (e.g., indicators)
  - `macro_indicators` (e.g., macro series)
- Refresh cadence: `daily` (recommended)

## Tech Stack
- **Backend:** Python 3.8+, Flask (inferred), scikit-learn, pandas, MLflow, SQLAlchemy
- **Frontend:** JavaScript, HTML, CSS
- **Database:** PostgreSQL (AWS RDS)
- **Containerization:** Docker, Docker Compose
- **CI/CD:** Github Actions
- **Testing:** pytest (backend), Jest or similar (frontend)

## Setup & Installation

### Prerequisites
- Python 3.8+
- Docker & Docker Compose (recommended for consistent local runs)

### Clone the Repository
```bash
git clone https://github.com/NateChris14/Finance-Web-App.git
cd Finance-Web-App
```

## Configuration

### Backend environment variables (required)

Configure these as environment variables (recommended) or via a secrets manager in production:

- DB_HOST = <aws-rds-endpoint>
- DB_PORT = 5432
- DB_NAME = <database-name>
- DB_USER = <username>
- DB_PASSWORD = <password>

### Running locally

#### Option A (recommended): Run using Docker Compose

This starts the backend and frontend containers. The backend container must be able to reach AWS RDS (networking/security group must allow it).

```bash
docker compose up --build
```

#### Option B:  Run backend + frontend without Docker

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd ../frontend
npm install  # If using npm for dependencies
```

### Running Locally
#### Backend
```bash
cd backend
python app.py
```

#### Frontend
```bash
cd frontend
# If using a dev server (e.g., live-server, http-server, or npm start)
npm start
# Or open index.html directly in your browser
```

## MLflow & Artifacts

- Ensure MLFLOW_TRACKING_URI is configured (local file store or remote server).
- MLflow runs and artifacts are stored in `mlruns/` and `mlartifacts/`.
- To view the MLflow UI:
```bash
mlflow ui
```

## Deployment (AWS ECS Fargate)

This project is containerized and deployed to AWS using:

- Docker images built for backend and frontend
- Images pushed to Amazon ECR
- Services/tasks running on Amazon ECS (Fargate)

High-level steps:

- Create ECR repositories
  - finance-web-app-backend (example)
  - finance-web-app-frontend (example)

- Build Docker images
  - Build backend and frontend images using their Dockerfiles (or via Docker Compose).

- Push images to ECR
  - Authenticate Docker to ECR using AWS CLI.
  - Tag and push both images to the correct ECR repositories.

- Create ECS cluster + task definitions
  - Define one service/task for backend and one for frontend (or a combined task if you run them together).
  - Configure environment variables/secrets for the backend DB connection.
  - Configure networking/security groups to allow backend → RDS connectivity.

- CI/CD with GitHub Actions
  - On pushes to main, GitHub Actions builds/tests and pushes updated images to ECR.
  - Then your workflow updates ECS to deploy the new task definition/image tags.

## Project Structure
```
FINAPP/
  backend/
    app.py            # Main backend application
    src/              # Source code (components, utils, etc.)
    artifacts/        # ML models and preprocessors
    data/             # Datasets
    tests/            # Backend tests
    requirements.txt  # Python dependencies
  frontend/
    index.html        # Main frontend entry
    app.js, api.js    # Frontend logic
    charts.js         # Visualization
    styles.css        # Styling
    tests/            # Frontend tests
  docker-compose.yml  # Multi-service orchestration
  README.md           # Project documentation
```

## Testing
### Backend
```bash
cd backend
pytest
```
### Frontend
```bash
cd frontend
# If using Jest or another test runner
npm test
```

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new features.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.





