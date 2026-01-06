[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Coverage](https://codecov.io/gh/NateChris14/Finance-Web-App/branch/main/graph/badge.svg)](https://codecov.io/gh/NateChris14/Finance-Web-App)
[![Last Commit](https://img.shields.io/github/last-commit/NateChris14/Finance-Web-App.svg)](https://github.com/NateChris14/Finance-Web-App/commits/main)

# Finance Web App

A full-stack finance web application for stock clustering, analysis, and visualization. This project leverages machine learning to cluster stocks and provides an interactive frontend for users to explore financial data and insights.

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

## Tech Stack
- **Backend:** Python, FastAPI/Flask (inferred), scikit-learn, pandas, MLflow
- **Frontend:** JavaScript, HTML, CSS
- **Containerization:** Docker, Docker Compose
- **Experiment Tracking:** MLflow
- **Testing:** pytest (backend), Jest or similar (frontend)

## Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js & npm (for frontend)
- Docker & Docker Compose (optional, for containerized setup)

### Clone the Repository
```bash
git clone <repo-url>
cd FINAPP
```

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

### Using Docker (Recommended)
```bash
docker-compose up --build
```
This will start both backend and frontend services.

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

## MLflow & Artifacts
- MLflow runs and artifacts are stored in `mlruns/` and `mlartifacts/`.
- To view the MLflow UI:
```bash
mlflow ui
```

## Deployment 

This project has been containerized using Docker and deployed to AWS ECS (Fargate). Below are the steps for deploying the application:

## 📊 Deployment Architecture

Below is the architecture used to deploy the Stock Intelligence Dashboard:

![Deployment Architecture](https://github.com/NateChris14/Finance-Web-App/blob/main/Deployment%20Architecture%20(Stock).png)

**Key components:**
- **AWS ECS (Fargate)**: For running containerized Flask app.
- **AWS ECR**: For storing the Docker images.
- **GitHub Actions**: For CI/CD pipeline to automatically deploy the app.
- **Flask App**: Exposes the dashboard to users via a web interface.
- **Docker**: Containerizes the application for deployment consistency across environments.


1. Dockerize the frontend and backend: Ensure the Dockerfiles are correctly set up in your project folder. Then build the Docker images:

```bash
docker build -t f1-pitstop-prediction .
```

2. Push Docker image to AWS ECR: Follow the steps to push your Docker image to AWS ECR:

* Create a repository on AWS ECR.

* Authenticate Docker to AWS using the AWS CLI.

* Push the image to ECR.

3. Set up AWS ECS:

* Create an ECS Cluster and Task Definition.

* Deploy your app using ECS Fargate.

4. Set up CI/CD with GitHub Actions: GitHub Actions will automatically deploy updates to AWS ECS whenever changes are pushed to the main branch.


## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new features.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.




