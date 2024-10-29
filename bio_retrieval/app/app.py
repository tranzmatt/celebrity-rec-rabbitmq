import os
import pika
import json
import requests  # Changed to use requests instead of http.client
import urllib.parse

RAPID_API_KEY = os.getenv('RAPID_API_KEY')

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

def get_wiki_infobox(celebrity_name):
    try:
        if not celebrity_name:
            raise ValueError("Celebrity name is empty")

        # Format the Wikipedia URL
        wiki_title = celebrity_name.replace(" ", "_")
        url = "https://wikipedia-infobox.p.rapidapi.com/infobox"
        
        querystring = {"wikiurl": f"https://en.wikipedia.org/wiki/{wiki_title}", "withname": "false"}

        headers = {
            "X-RapidAPI-Key": RAPID_API_KEY,
            "X-RapidAPI-Host": "wikipedia-infobox.p.rapidapi.com"
        }

        print(f"Making API request for {celebrity_name}")
        response = requests.get(url, headers=headers, params=querystring)
        print(f"API response status: {response.status_code}")
        
        if response.status_code != 200:
            raise ValueError(f"API returned status code {response.status_code}")

        raw_data = response.json()
        print(f"Raw API response: {json.dumps(raw_data, indent=2)}")
        
        # Create structured biography data
        bio_data = {
            "celebrity": celebrity_name,
            "personal_info": {
                "birth": raw_data.get("Born", {}).get("value") if isinstance(raw_data.get("Born"), dict) else raw_data.get("Born", "Birth information not available"),
                "occupation": raw_data.get("Occupations", "Occupation not available"),
                "years_active": raw_data.get("Years active", "Years active not available"),
                "citizenship": raw_data.get("Citizenship", "Citizenship not available")
            },
            "career": {
                "has_awards": "Awards" in raw_data,
                "filmography": raw_data.get("Works", {}).get("url", "Filmography not available") if isinstance(raw_data.get("Works"), dict) else "Filmography not available"
            },
            "relationships": {
                "partner": raw_data.get("Partner", {}).get("value", "Partner information not available") if isinstance(raw_data.get("Partner"), dict) else raw_data.get("Partner", "Partner information not available"),
                "children": raw_data.get("Children", "Children information not available")
            }
        }
        
        print(f"Structured bio data: {json.dumps(bio_data, indent=2)}")
        return bio_data
        
    except Exception as e:
        print(f"Error getting wiki info: {str(e)}")
        return {
            "celebrity": celebrity_name,
            "error": True,
            "message": f"Unable to fetch biography for {celebrity_name}",
            "details": str(e),
            "personal_info": {
                "birth": "Information unavailable",
                "occupation": "Information unavailable",
                "years_active": "Information unavailable",
                "citizenship": "Information unavailable"
            },
            "career": {
                "has_awards": False,
                "filmography": "Information unavailable"
            },
            "relationships": {
                "partner": "Information unavailable",
                "children": "Information unavailable"
            }
        }

def callback(ch, method, properties, body):
    try:
        celebrity_name = body.decode()
        print(f"Getting bio for: {celebrity_name}")
        
        bio_data = get_wiki_infobox(celebrity_name)
        
        # Send bio to bio_queue
        connection = create_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='bio_queue', durable=True)
        
        json_data = json.dumps(bio_data)
        print(f"Sending to bio_queue: {json_data}")
        
        channel.basic_publish(
            exchange='',
            routing_key='bio_queue',
            body=json_data,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        connection.close()
        print(f"Sent bio to bio_queue for {celebrity_name}")
        
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        error_data = {
            "celebrity": celebrity_name if 'celebrity_name' in locals() else "Unknown",
            "error": True,
            "message": "Failed to process biography",
            "details": str(e),
            "personal_info": {
                "birth": "Error occurred",
                "occupation": "Error occurred",
                "years_active": "Error occurred",
                "citizenship": "Error occurred"
            },
            "career": {
                "has_awards": False,
                "filmography": "Error occurred"
            },
            "relationships": {
                "partner": "Error occurred",
                "children": "Error occurred"
            }
        }
        connection = create_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='bio_queue', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='bio_queue',
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
    
    print('Bio service waiting for celebrity names from fanout exchange. To exit press CTRL+C')
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
