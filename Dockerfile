# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

## Temp install git unless django-celery-beat don't support DJango 5.0 (check requirements.txt)
#RUN apt update && apt install -y git

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/
