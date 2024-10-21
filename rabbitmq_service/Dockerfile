# Use the official RabbitMQ image as the base image
FROM rabbitmq:3-management

# Copy the initialization script into the container
COPY init.sh /init.sh

# Make the script executable
RUN chmod +x /init.sh

# Set the entrypoint to our init script
ENTRYPOINT ["/init.sh"]
