#!/bin/bash

# 領頭羊博士 - 自動化部署腳本
# 此腳本用於一鍵部署整個應用程式到生產環境

# 切換到腳本目錄
cd "$(dirname "$0")"

echo "Starting Goat Nutrition App Deploy..."
echo "====================================="
echo "Press Enter to continue..."
read -r

# 檢查 Docker 是否安裝
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker not installed"
    echo "Please manually install Docker"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
else
    echo "Docker found"
    docker --version
fi

echo "All checks complete"
echo "Press Enter to continue..."
read -r

echo "Checking if Docker service is ready..."
if ! docker info >/dev/null 2>&1; then
    echo "Docker service is not ready yet."
    echo "Please make sure Docker is running and try again."
    exit 1
fi

echo "Docker service is ready!"
echo ""

# Check Docker Compose
echo "Checking Docker Compose..."
if command -v "docker compose" &> /dev/null && docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "SUCCESS: Docker Compose available"
elif command -v docker-compose &> /dev/null && docker-compose --version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "SUCCESS: Docker Compose legacy version available"
else
    echo "ERROR: Docker Compose not installed"
    exit 1
fi
echo ""

# Check environment file
echo "Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env configuration file..."
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://goat_user:goat_password@db:5432/goat_nutrition_db
POSTGRES_DB=goat_nutrition_db
POSTGRES_USER=goat_user
POSTGRES_PASSWORD=goat_password

# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=production
FLASK_DEBUG=False

# CORS Configuration
CORS_ORIGINS=http://localhost,http://127.0.0.1

# Google Gemini API
GOOGLE_API_KEY=your-gemini-api-key

# Log Configuration
LOG_LEVEL=INFO
EOF
    echo "SUCCESS: .env file created with default settings"
else
    echo "SUCCESS: .env file already exists"
fi
echo ""

echo "SUCCESS: All environment checks completed"
echo "Starting deployment process..."
echo ""

# Stop existing containers
echo "Step 1: Stopping existing containers..."
$DOCKER_COMPOSE_CMD down
echo ""

# Build images
echo "Step 2: Building application images..."
$DOCKER_COMPOSE_CMD build --no-cache
echo ""

# Start services
echo "Step 3: Starting services..."
$DOCKER_COMPOSE_CMD up -d
echo ""

# Wait for database
echo "Step 4: Waiting for database to initialize - 15 seconds..."
sleep 15
echo ""

# Run database migration
echo "Step 5: Running database migration..."
$DOCKER_COMPOSE_CMD exec -T backend flask db upgrade
echo ""

# Check service status
echo "Step 6: Checking service status..."
$DOCKER_COMPOSE_CMD ps
echo ""

# Wait for application
echo "Step 7: Waiting for application to fully start - 10 seconds..."
sleep 10
echo ""

echo "========================================"
echo "DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "========================================"
echo ""
echo "Your application is now running:"
echo "Frontend: http://localhost"
echo "API: http://localhost/api"
echo ""
echo "Management commands:"
echo "View logs: $DOCKER_COMPOSE_CMD logs -f"
echo "Stop services: $DOCKER_COMPOSE_CMD down"
echo "Restart services: $DOCKER_COMPOSE_CMD restart"
echo ""
echo "Account notice:"
echo "Please register a new account via the UI or API (/api/auth/register) before login."
echo ""
echo "Press Enter to exit..."
read -r
