# Use an official Python runtime as the base image
FROM python:3.12-slim

# Install the required packages
RUN pip install --no-cache-dir pika pillow requests pymediawiki pywikibot

# Copy the current directory contents into the container at /app
ADD app /app

# Set the working directory in the container
WORKDIR /app

# Run app.py when the container launches
CMD ["python", "-u", "app.py"]
