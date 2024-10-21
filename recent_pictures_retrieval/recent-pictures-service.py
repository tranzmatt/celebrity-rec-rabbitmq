# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]

# requirements.txt
pika
requests

# app.py
import os
import pika
import requests
import json

def fetch_recent_photos(name):
    # This is a placeholder. In a real application, you'd query an API or image search service.
    return [f"photo_url_{i}.jpg" for i in range(5)]

def callback(ch, method, properties, body):
    celebrity_name = body.decode()
    recent_photos = fetch_recent_photos(celebrity_name)
    
    # Publish result to the pictures_queue
    channel.basic_publish(exchange='', routing_key='pictures_queue', body=json.dumps(recent_photos))

connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost')))
channel = connection.channel()

channel.queue_declare(queue='name_queue')
channel.queue_declare(queue='pictures_queue')

channel.basic_consume(queue='name_queue', on_message_callback=callback, auto_ack=True)

print('Recent Pictures Retrieval Service is waiting for messages. To exit press CTRL+C')
channel.start_consuming()
