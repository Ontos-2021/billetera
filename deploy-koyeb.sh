#!/bin/bash

echo "🚀 MoneyFlow Mirror - Koyeb Deployment Script"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Make sure you're in the project root."
    exit 1
fi

# Check if Koyeb CLI is installed
if ! command -v koyeb &> /dev/null; then
    echo "❌ Koyeb CLI not found. Please install it first:"
    echo "   curl -fsSL https://cli.koyeb.com/installer.sh | sh"
    exit 1
fi

echo "📦 Building and pushing to Git..."
git add .
git commit -m "Deploy to Koyeb $(date)"
git push origin main

echo "🔧 Creating Koyeb application..."
koyeb app create moneyflow || echo "App already exists, continuing..."

echo "🗄️ Creating PostgreSQL database..."
koyeb database create postgres moneyflow-db --plan free || echo "Database already exists, continuing..."

echo "⚙️ Getting database URL..."
DB_URL=$(koyeb database get moneyflow-db --output json | jq -r '.connection_string')

echo "🌐 Setting environment variables..."
koyeb secret create SECRET_KEY $(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
koyeb secret create DATABASE_URL "$DB_URL"

echo "🚀 Deploying service..."
koyeb service create --app moneyflow web --git github.com/Ontos-2021/billetera --git-branch main --docker-dockerfile Dockerfile --port 8000 --instance-type shared-cpu-1x

echo "✅ Deployment started! Check status with: koyeb service list"
echo "🌍 Your app will be available at: https://moneyflow-<org>.koyeb.app"
