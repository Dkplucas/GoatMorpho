FROM python:3.12-slim-bullseye AS production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set build-time environment variable for collectstatic
ENV SECRET_KEY="build_time_secret_key_123"
ENV DEBUG=0
ENV DJANGO_SETTINGS_MODULE=goat_measure.settings

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Command to run in container
CMD ["gunicorn", "goat_measure.wsgi:application", "--bind", "0.0.0.0:8000"]