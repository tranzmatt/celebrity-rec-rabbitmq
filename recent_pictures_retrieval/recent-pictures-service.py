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

credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'myuser'), os.environ.get('RABBITMQ_PASS', 'mypassword'))
parameters = pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost'), credentials=credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.queue_declare(queue='name_queue', durable=True)
channel.queue_declare(queue='pictures_queue', durable=True)

channel.basic_consume(queue='name_queue', on_message_callback=callback, auto_ack=True)

print('Recent Pictures Retrieval Service is waiting for messages. To exit press CTRL+C')
channel.start_consuming()
