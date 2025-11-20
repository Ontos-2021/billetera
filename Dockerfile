# MoneyFlow Mirror Dockerfile for Koyeb Deployment
FROM python:3.11-slim

# Usá Python sin buffer
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependencies file
COPY requirements.txt .

# Install Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Change to Django project directory
WORKDIR /app/billetera

# Run migrations, collect static, then start Gunicorn
CMD ["/entrypoint.sh"]
