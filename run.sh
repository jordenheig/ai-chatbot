#!/bin/bash

# Create and activate virtual environment
# python -m venv venv
# source venv/bin/activate

# Install dependencies
#pip install -r requirements.txt

# Initialize database
python -m app.db.init_db

# Start services using docker-compose
docker-compose -f docker/docker-compose.yml up --build 
