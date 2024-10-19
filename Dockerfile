# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set environment variables for PostgreSQL
ENV POSTGRES_DB=kyrt_dev
ENV POSTGRES_USER=recevo
ENV POSTGRES_PASSWORD=evo2compm3194256121

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/
