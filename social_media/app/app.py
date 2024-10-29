#!/usr/bin/python3
import os
import pika
import json
import pywikibot
import re


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


def get_social_media_links(celebrity_name):
    try:
        # Initialize the Wikipedia page and get social media links
        site = pywikibot.Site("en", "wikipedia")
        page = pywikibot.Page(site, celebrity_name)

        # Social media patterns
        social_media_patterns = {
            'X': re.compile(r'x\.com/[\w]+'),
            'Twitter': re.compile(r'twitter\.com/[\w]+'),
            'Instagram': re.compile(r'instagram\.com/[\w]+'),
            'Facebook': re.compile(r'facebook\.com/[\w]+'),
            'YouTube': re.compile(r'youtube\.com/(user|channel)/[\w-]+'),
            'LinkedIn': re.compile(r'linkedin\.com/in/[\w-]+'),
            'TikTok': re.compile(r'tiktok\.com/@[\w-]+')
        }

        # Get external links from the Wikipedia page
        external_links = page.extlinks()
        social_links = {}

        # Find matching social media links
        for link in external_links:
            for platform, pattern in social_media_patterns.items():
                if pattern.search(link):
                    social_links[platform] = link
                    break  # Stop once a match is found for this link

        # Return structured data
        return {
            "celebrity": celebrity_name,
            "social_media": social_links
        }

    except Exception as e:
        print(f"Error retrieving social media links: {str(e)}")
        return {
            "celebrity": celebrity_name,
            "error": True,
            "message": f"Unable to fetch social media links for {celebrity_name}",
            "details": str(e)
        }


def callback(ch, method, properties, body):
    try:
        celebrity_name = body.decode()
        print(f"Getting social media links for: {celebrity_name}")

        social_data = get_social_media_links(celebrity_name)

        # Send social media data to social_queue
        connection = create_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='social_queue', durable=True)

        json_data = json.dumps(social_data)
        print(f"Sending to social_queue: {json_data}")

        channel.basic_publish(
            exchange='',
            routing_key='social_queue',
            body=json_data,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        connection.close()
        print(f"Sent social media links to social_queue for {celebrity_name}")

    except Exception as e:
        print(f"Error in callback: {str(e)}")
        error_data = {
            "celebrity": celebrity_name if 'celebrity_name' in locals() else "Unknown",
            "error": True,
            "message": "Failed to process social media links",
            "details": str(e),
            "social_media": {}
        }
        connection = create_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='social_queue', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='social_queue',
            body=json.dumps(error_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        connection.close()
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    # Set up RabbitMQ connection
    connection = create_rabbitmq_connection()
    channel = connection.channel()

    # Declare the celebrity_names exchange
    channel.exchange_declare(
        exchange='celebrity_names',
        exchange_type='fanout',
        durable=True
    )

    # Create an exclusive queue for this consumer
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # Bind our exclusive queue to the celebrity_names exchange
    channel.queue_bind(
        exchange='celebrity_names',
        queue=queue_name
    )

    # Set up consumer on our exclusive queue
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=False
    )

    print('Social media service waiting for celebrity names from fanout exchange. To exit press CTRL+C')
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
