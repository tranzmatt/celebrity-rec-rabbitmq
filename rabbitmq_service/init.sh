#!/bin/bash

# Start RabbitMQ in the background
rabbitmq-server &

# Wait for RabbitMQ to start
sleep 15

# Create exchanges
rabbitmqctl exchange_declare celebrity_names fanout --durable

# Create queues
rabbitmqctl queue_declare image_queue --durable
rabbitmqctl queue_declare name_queue --durable
rabbitmqctl queue_declare bio_queue --durable
rabbitmqctl queue_declare pictures_queue --durable
rabbitmqctl queue_declare result_queue --durable

# Bind name_queue to celebrity_names exchange
rabbitmqctl queue_bind name_queue --exchange=celebrity_names

# Create user and set permissions (if not using default guest user)
rabbitmqctl add_user myuser mypassword
rabbitmqctl set_user_tags myuser administrator
rabbitmqctl set_permissions -p / myuser ".*" ".*" ".*"

# Keep the container running
tail -f /var/lib/rabbitmq/mnesia/rabbit@rabbitmq.log
