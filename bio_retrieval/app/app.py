# app.py
import os
import pika
import requests

def fetch_celebrity_bio(name):
    # This is a placeholder. In a real application, you'd query an API or database for the bio.
    return f"This is a bio for {name}."

def callback(ch, method, properties, body):
    celebrity_name = body.decode()
    bio = fetch_celebrity_bio(celebrity_name)
    
    # Publish result to the bio_queue
    channel.basic_publish(exchange='', routing_key='bio_queue', body=bio)

connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost')))
channel = connection.channel()

channel.queue_declare(queue='name_queue')
channel.queue_declare(queue='bio_queue')

channel.basic_consume(queue='name_queue', on_message_callback=callback, auto_ack=True)

print('Bio Retrieval Service is waiting for messages. To exit press CTRL+C')
channel.start_consuming()
