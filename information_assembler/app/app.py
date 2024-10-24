# app.py
import os
import pika
import json

def callback(ch, method, properties, body):
    global celebrity_name, bio, recent_pictures

    if method.routing_key == 'name_queue':
        celebrity_name = body.decode()
    elif method.routing_key == 'bio_queue':
        bio = body.decode()
    elif method.routing_key == 'pictures_queue':
        recent_pictures = json.loads(body)

    if celebrity_name and bio and recent_pictures:
        assembled_info = {
            'name': celebrity_name,
            'bio': bio,
            'recent_pictures': recent_pictures
        }
        channel.basic_publish(exchange='', routing_key='result_queue', body=json.dumps(assembled_info))
        celebrity_name, bio, recent_pictures = None, None, None


credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'myuser'), os.environ.get('RABBITMQ_PASS', 'mypassword'))
parameters = pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost'), credentials=credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.queue_declare(queue='name_queue', durable=True)
channel.queue_declare(queue='bio_queue', durable=True)
channel.queue_declare(queue='pictures_queue', durable=True)
channel.queue_declare(queue='result_queue', durable=True)

channel.basic_consume(queue='name_queue', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue='bio_queue', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue='pictures_queue', on_message_callback=callback, auto_ack=True)

celebrity_name, bio, recent_pictures = None, None, None

print('Information Assembler Service is waiting for messages. To exit press CTRL+C')
channel.start_consuming()
