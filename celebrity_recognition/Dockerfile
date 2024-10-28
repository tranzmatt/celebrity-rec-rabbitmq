# Use an official Python runtime as the base image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    software-properties-common \
    bind9-dnsutils \
    net-tools \
    git \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the required packages
RUN pip install --no-cache-dir face_recognition pika pillow requests

# Copy the current directory contents into the container at /app
ADD app /app

# Set the working directory in the container
WORKDIR /app

# Run app.py when the container launches
CMD ["python", "-u", "app.py"]
