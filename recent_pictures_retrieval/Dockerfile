# Use an official Python runtime as the base image
FROM python:3.12-slim

# Copy the current directory contents into the container at /app
ADD app /app

# Set the working directory in the container
WORKDIR /app

# Install the required packages
RUN pip install --no-cache-dir pika pillow requests

# Run app.py when the container launches
CMD ["python", "app.py"]
