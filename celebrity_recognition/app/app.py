import os
import requests
import json
import pika
import tempfile

API_ENDPOINT = "https://imagerecognize.com/api/v3/"
API_KEY = os.getenv('IMAGE_RECOGNIZE_API_KEY')

def create_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        os.environ.get('RABBITMQ_USER', 'myuser'),
        os.environ.get('RABBITMQ_PASS', 'mypassword')
    )
    parameters = pika.ConnectionParameters(
        host=os.environ.get('RABBITMQ_HOST', 'localhost'),
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)

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
        print(f"We got response {response}")
        try:
            objects = response['data']['objects']
            if objects:
                highest_confidence_object = max(objects, key=lambda obj: obj['confidence'])
                print(highest_confidence_object['name'])
                return highest_confidence_object['name']
            else:
                print("No celebrities found in the image.")
                return "No celebrities found in the image."
        except KeyError as e:
            print(f"KeyError {e}")
            return "Unexpected response structure."
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def callback(ch, method, properties, body):
    print('Calling recognize_celebrity')
    result = recognize_celebrity(body)
    print(f'Sending result: {result}')
    
    # Send result to celebrity_names exchange
    connection = create_rabbitmq_connection()
    channel = connection.channel()
    
    # Declare the fanout exchange
    channel.exchange_declare(
        exchange='celebrity_names',
        exchange_type='fanout',
        durable=True
    )
    
    # Publish the result to the exchange
    channel.basic_publish(
        exchange='celebrity_names',
        routing_key='',  # Not needed for fanout exchange
        body=result,
        properties=pika.BasicProperties(
            delivery_mode=2  # make message persistent
        )
    )
    
    # Also send to result_queue for the UI
    channel.queue_declare(queue='result_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='result_queue',
        body=result,
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )
    
    connection.close()

def main():
    # Set up RabbitMQ connection
    connection = create_rabbitmq_connection()
    channel = connection.channel()
    
    # Declare the queues we need
    channel.queue_declare(queue='image_queue', durable=True)
    
    # Set up consumer
    channel.basic_consume(
        queue='image_queue',
        auto_ack=True,
        on_message_callback=callback
    )
    
    print('Waiting for images. To exit press CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            connection.close()
        except:
            pass

if __name__ == "__main__":
    main()
