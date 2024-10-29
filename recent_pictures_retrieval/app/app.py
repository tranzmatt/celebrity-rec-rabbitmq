import os
import time
import pika

credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_USER', 'myuser'), os.environ.get('RABBITMQ_PASS', 'mypassword'))
parameters = pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'), credentials=credentials)
connection = pika.BlockingConnection(parameters)


while True:
    time.sleep(10)


