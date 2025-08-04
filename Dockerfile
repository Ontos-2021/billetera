# MoneyFlow Mirror Dockerfile for Koyeb Deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Change to Django project directory
WORKDIR /app/billetera

# Expose port (Koyeb uses PORT environment variable)
ENV PORT=8000

# Run migrations, collect static, then start Gunicorn
CMD ["/entrypoint.sh"]
