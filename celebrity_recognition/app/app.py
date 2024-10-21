import os
import requests
import json
import pika
import tempfile

API_ENDPOINT = "https://imagerecognize.com/api/v3/"
API_KEY = os.getenv('IMAGE_RECOGNIZE_API_KEY')

def recognize_celebrity(image_data):
    # Create a temporary file to store the image data
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(image_data)
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, 'rb') as f1:
            f = {'file': f1.read()}
        d = {
            'apikey': API_KEY,
            'type': 'celebrities',
            'max_labels': 10,
            'min_confidence': 80
        }
        r = requests.post(url=API_ENDPOINT, data=d, files=f)
        response = json.loads(r.text)
        try:
            objects = response['data']['objects']
            if objects:
                highest_confidence_object = max(objects, key=lambda obj: obj['confidence'])
                return highest_confidence_object['name']
            else:
                return "No celebrities found in the image."
        except KeyError:
            return "Unexpected response structure."
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def callback(ch, method, properties, body):
    result = recognize_celebrity(body)
    
    # Send result back
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='result_queue')
    channel.basic_publish(exchange='',
                          routing_key='result_queue',
                          body=result)
    connection.close()

# Set up RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='image_queue')
channel.basic_consume(queue='image_queue',
                      auto_ack=True,
                      on_message_callback=callback)

print('Waiting for images. To exit press CTRL+C')
channel.start_consuming()
