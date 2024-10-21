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

connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost')))
channel = connection.channel()

channel.queue_declare(queue='name_queue')
channel.queue_declare(queue='bio_queue')
channel.queue_declare(queue='pictures_queue')
channel.queue_declare(queue='result_queue')

channel.basic_consume(queue='name_queue', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue='bio_queue', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue='pictures_queue', on_message_callback=callback, auto_ack=True)

celebrity_name, bio, recent_pictures = None, None, None

print('Information Assembler Service is waiting for messages. To exit press CTRL+C')
channel.start_consuming()
