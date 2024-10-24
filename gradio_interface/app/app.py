# app.py
import os
import gradio as gr
import pika
import json
from PIL import Image
import io

def setup_rabbitmq():
    credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'myuser'), os.environ.get('RABBITMQ_PASS', 'mypassword'))
    parameters = pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost'), credentials=credentials)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(queue='upload_queue', durable=True)
    channel.queue_declare(queue='result_queue', durable=True)
    return connection, channel

def process_image(image):
    connection, channel = setup_rabbitmq()

    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Send image to recognition service
    channel.basic_publish(exchange='', routing_key='upload_queue', body=img_byte_arr)

    # Wait for the result
    method_frame, header_frame, body = channel.basic_get(queue='result_queue', auto_ack=True)
    
    if method_frame:
        result = json.loads(body)
        connection.close()
        return f"Celebrity: {result['name']}\nBio: {result['bio']}\nRecent Pictures: {', '.join(result['recent_pictures'])}"
    else:
        connection.close()
        return "No result received"

iface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Celebrity Recognition System"
)

iface.launch(server_name="0.0.0.0", server_port=7860)
