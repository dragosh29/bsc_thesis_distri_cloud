# Base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    docker.io \
    && apt-get clean

# Copy requirements
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Run migrations and start the server with live reload
CMD ["sh", "-c", "python manage.py migrate && watchgod manage:main"]
