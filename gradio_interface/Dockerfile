# Use an official Python runtime as the base image
FROM python:3.12-slim

# Install the required packages
RUN pip install --no-cache-dir gradio pika pillow requests

# Copy the current directory contents into the container at /app
ADD app /app

# Set the working directory in the container
WORKDIR /app

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Run app.py when the container launches
CMD ["python", "-u", "app.py"]
#CMD ["python", "-u", "test.py"]
