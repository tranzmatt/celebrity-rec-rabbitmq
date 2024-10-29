import os
import gradio as gr
import pika
import json
from PIL import Image
import io
import time
import threading
import asyncio

def create_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        os.environ.get('RABBITMQ_USER', 'myuser'),
        os.environ.get('RABBITMQ_PASS', 'mypassword')
    )
    parameters = pika.ConnectionParameters(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)

class CelebRecognitionUI:
    def __init__(self):
        self.current_name = ""
        self.current_bio = ""
        self.current_social = ""

    async def listen_for_names(self):
        while True:
            try:
                connection = create_rabbitmq_connection()
                channel = connection.channel()
                channel.queue_declare(queue='name_queue', durable=True)

                def callback(ch, method, properties, body):
                    try:
                        name = body.decode()
                        print(f"Received name: {name}")
                        self.current_name = name
                        print(f"Updated current_name to: {self.current_name}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing name: {e}")

                channel.basic_consume(
                    queue='name_queue',
                    on_message_callback=callback,
                    auto_ack=False
                )

                print("Listening for names on name_queue...")
                channel.start_consuming()

            except Exception as e:
                print(f"Name listener error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    async def listen_for_social(self):
        while True:
            try:
                connection = create_rabbitmq_connection()
                channel = connection.channel()
                channel.queue_declare(queue='social_queue', durable=True)

                def callback(ch, method, properties, body):
                    try:
                        social = body.decode()
                        print(f"Received name: {social}")
                        self.current_social = social
                        print(f"Updated current_name to: {self.current_social}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing name: {e}")

                channel.basic_consume(
                    queue='social_queue',
                    on_message_callback=callback,
                    auto_ack=False
                )

                print("Listening for social on social_queue...")
                channel.start_consuming()

            except Exception as e:
                print(f"Social listener error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    async def listen_for_bios(self):
        while True:
            try:
                connection = create_rabbitmq_connection()
                channel = connection.channel()
                channel.queue_declare(queue='bio_queue', durable=True)

                def callback(ch, method, properties, body):
                    try:
                        bio_data = json.loads(body)
                        print(f"Received bio: {bio_data}")

                        if "error" in bio_data and bio_data["error"]:
                            bio_text = f"Error: {bio_data.get('message', 'Unknown error')}"
                        else:
                            personal = bio_data.get("personal_info", {})
                            career = bio_data.get("career", {})
                            relationships = bio_data.get("relationships", {})

                            bio_parts = []
                            if personal.get("birth"):
                                bio_parts.append(f"Birth: {personal['birth']}")
                            if personal.get("occupation"):
                                bio_parts.append(f"Occupation: {personal['occupation']}")
                            if personal.get("years_active"):
                                bio_parts.append(f"Years active: {personal['years_active']}")
                            if career.get("has_awards"):
                                bio_parts.append("Has received awards and accolades")
                            if relationships.get("partner"):
                                bio_parts.append(f"Partner: {relationships['partner']}")

                            bio_text = " | ".join(bio_parts)

                        print(f'Setting bio text: {bio_text}')
                        self.current_bio = bio_text
                        print(f"Updated current_bio to: {self.current_bio}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                    except Exception as e:
                        print(f"Error processing bio: {e}")

                channel.basic_consume(
                    queue='bio_queue',
                    on_message_callback=callback,
                    auto_ack=False
                )

                print("Listening for bios on bio_queue...")
                channel.start_consuming()

            except Exception as e:
                print(f"Bio listener error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def process_image(self, image):
        if image is None:
            return "No image provided", "", ""

        try:
            print("Processing image...")
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            connection = create_rabbitmq_connection()
            channel = connection.channel()

            channel.basic_publish(
                exchange='',
                routing_key='image_queue',
                body=img_byte_arr,
                properties=pika.BasicProperties(
                    delivery_mode=2
                )
            )

            connection.close()
            print("Image sent to processing queue")

            # Clear the current values
            self.current_name = ""
            self.current_bio = ""

            return "Processing image...", "", ""

        except Exception as e:
            print(f"Error processing image: {e}")
            return f"Error: {str(e)}", "", ""

    # Generator function for real-time updates
    def get_current_values(self):
        while True:
            yield self.current_name, self.current_bio
            time.sleep(1)  # Update every second


# Create the Gradio interface
with gr.Blocks(title="Celebrity Recognition System") as iface:
    with gr.Row():
        image_input = gr.Image(type="pil", label="Upload Image")

    with gr.Row():
        name_output = gr.Textbox(label="Celebrity Name", value="")
        bio_output = gr.Textbox(label="Celebrity Biography", value="")

    with gr.Row():
        social_output = gr.Textbox(label="Celebrity Social Media", value="")

    status_output = gr.Textbox(label="Status", value="Ready")
    submit_btn = gr.Button("Submit")

    # Create instance of our UI class
    ui = CelebRecognitionUI()

    # Start the listeners
    threading.Thread(target=lambda: asyncio.run(ui.listen_for_names()), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(ui.listen_for_bios()), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(ui.listen_for_social()), daemon=True).start()

    # Set up the events
    submit_btn.click(
        fn=ui.process_image,
        inputs=image_input,
        outputs=[status_output, name_output, bio_output, social_output]
    )

    # Periodically update name and bio outputs using the generator
    iface.load(ui.get_current_values, inputs=None, outputs=[name_output, bio_output, social_output])

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
