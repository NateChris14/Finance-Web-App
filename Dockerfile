#Python 3.12 as base image
FROM python:3.12-slim

#Setting up the working directory
WORKDIR /app

#Copying the working directory
COPY . /app

#Upgrading pip and installing dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

#Setting the environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0
ENV PORT=8050

#Exposing the port
EXPOSE 8050

#Running the flask app with memory-efficient settings
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "100", "app:server"]

