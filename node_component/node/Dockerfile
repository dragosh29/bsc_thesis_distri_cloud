# Base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the local API port
EXPOSE 18001

# Start the Node Local API
CMD ["python", "node_local_server.py"]
