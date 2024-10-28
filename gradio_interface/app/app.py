import os
import gradio as gr
import pika
import json
from PIL import Image
import io
import time

response = None  # Global variable to store the result


def callback(ch, method, properties, body):
    global response
    # Log the body for debugging
    print(f"Received body: {body}")

    # Check if body is not empty and decode it
    if body:
        try:
            response = body.decode()
            print(f"Decoded response: {response}")
        except UnicodeDecodeError as e:
            print(f"Failed to decode response: {e}")
            response = "Error: Unable to decode response"
    else:
        print("Received empty body")
        response = "Error: Empty response received"

    ch.basic_ack(delivery_tag=method.delivery_tag)

def process_image(image):
    global response
    response = None  # Reset the response for each image

    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Send image to recognition service
    credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'myuser'), os.environ.get('RABBITMQ_PASS', 'mypassword'))
    parameters = pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost'), credentials=credentials)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(queue='image_queue', durable=True)
    channel.queue_declare(queue='result_queue', durable=True)

    channel.basic_publish(exchange='', routing_key='image_queue', body=img_byte_arr)

    # Start consuming the result
    channel.basic_consume(queue='result_queue', on_message_callback=callback, auto_ack=False)

    print("Waiting for result...")
    # Check for result for up to 30 seconds
    for _ in range(30):
        connection.process_data_events(time_limit=1)  # Wait for a message for 1 second
        if response:
            break  # Exit loop if a response is received

    connection.close()

    # Debugging step: Print the raw response
    print(f"Received response: {response}")

    if response:
        return f"{response}"
    else:
        return "No result received after timeout"

iface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Celebrity Recognition System"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)

