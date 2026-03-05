#!/bin/bash

echo "🚀 Starting Cenvi Backend with MySQL..."

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down -v

# Build and start new containers
echo "🔨 Building and starting containers..."
docker-compose up --build -d

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL to start..."
sleep 10

# Check MySQL connection
echo "🔍 Testing MySQL connection..."
docker exec -it cenvi_mysql mysql -u cenvi_user -pcenvi_pass_2024 -e "SHOW DATABASES;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ MySQL connection successful!"
else
    echo "❌ MySQL connection failed!"
fi

# Show logs
echo "📋 Showing server logs..."
docker-compose logs -f server
