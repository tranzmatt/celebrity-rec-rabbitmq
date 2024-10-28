#!/bin/bash

# Start RabbitMQ in the background
rabbitmq-server &

# Wait for RabbitMQ to start
sleep 15

# Create queues
rabbitmqctl declare_queue name=image_queue
rabbitmqctl declare_queue name=name_queue
rabbitmqctl declare_queue name=bio_queue
rabbitmqctl declare_queue name=pictures_queue
rabbitmqctl declare_queue name=result_queue

# Create user and set permissions (if not using default guest user)
# rabbitmqctl add_user myuser mypassword
# rabbitmqctl set_user_tags myuser administrator
# rabbitmqctl set_permissions -p / myuser ".*" ".*" ".*"

# Keep the container running
tail -f /dev/null
