FROM rabbitmq:3-management

# Copy configuration files
COPY conf/definitions.json /etc/rabbitmq/definitions.json
COPY init.sh /init.sh

# Make the script executable
RUN chmod +x /init.sh

# Set environment variable to load definitions
ENV RABBITMQ_DEFINITIONS_FILE=/etc/rabbitmq/definitions.json

# Expose ports
EXPOSE 5672 15672

# Set the entry point to our init script
CMD ["/init.sh"]
