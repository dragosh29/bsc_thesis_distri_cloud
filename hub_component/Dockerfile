FROM python:3.12

# System dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    docker.io \
    python3-venv \
    && apt-get clean

# Setup working directory
WORKDIR /app

# Set up Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies inside virtual environment
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && watchgod manage:main"]
