@echo off
REM Removed chcp command that might cause issues
cd /d "%~dp0"

echo Starting Goat Nutrition App Deploy...
echo =====================================
pause

echo Checking winget...
winget --version >nul 2>&1
if errorlevel 1 (
    echo winget not found - will skip auto-install
    set SKIP_WINGET=1
    pause
) else (
    echo winget found
    winget --version
)

echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker not installed
    if defined SKIP_WINGET (
        echo Please manually install Docker Desktop
        pause
        exit /b 1
    )
    echo Installing Docker...
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
) else (
    echo Docker found
    docker --version
)

echo All checks complete
pause

echo Docker Desktop has been installed.
echo Please follow these steps:
echo 1. Restart your computer if this is the first Docker installation
echo 2. Manually start Docker Desktop from the desktop icon
echo 3. Wait for Docker Desktop to fully load (whale icon in system tray)
echo 4. Then press any key to continue with deployment
echo.
pause

echo Checking if Docker service is ready...
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker service is not ready yet.
    echo Please make sure Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo Docker service is ready!
echo.

REM Check Docker Compose
echo Checking Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Docker Compose not installed
        pause
        exit /b 1
    ) else (
        set DOCKER_COMPOSE_CMD=docker-compose
        echo SUCCESS: Docker Compose legacy version available
    )
) else (
    set DOCKER_COMPOSE_CMD=docker compose
    echo SUCCESS: Docker Compose available
)
echo.

REM Check environment file
echo Checking environment configuration...
if not exist ".env" (
    echo Creating .env configuration file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql://goat_user:goat_password@db:5432/goat_nutrition_db
        echo POSTGRES_DB=goat_nutrition_db
        echo POSTGRES_USER=goat_user
        echo POSTGRES_PASSWORD=goat_password
        echo.
        echo # Flask Configuration
        echo SECRET_KEY=your-secret-key-change-in-production
        echo FLASK_ENV=production
        echo FLASK_DEBUG=False
        echo.
        echo # CORS Configuration
        echo CORS_ORIGINS=http://localhost,http://127.0.0.1
        echo.
        echo # Google Gemini API
        echo GOOGLE_API_KEY=your-gemini-api-key
        echo.
        echo # Log Configuration
        echo LOG_LEVEL=INFO
    ) > .env
    echo SUCCESS: .env file created with default settings
) else (
    echo SUCCESS: .env file already exists
)
echo.

echo SUCCESS: All environment checks completed
echo Starting deployment process...
echo.

REM Stop existing containers
echo Step 1: Stopping existing containers...
%DOCKER_COMPOSE_CMD% down
echo.

REM Build images
echo Step 2: Building application images...
%DOCKER_COMPOSE_CMD% build --no-cache
echo.

REM Start services
echo Step 3: Starting services...
%DOCKER_COMPOSE_CMD% up -d
echo.

REM Wait for database
echo Step 4: Waiting for database to initialize - 15 seconds...
timeout /t 15 /nobreak >nul
echo.

REM Database migration is now handled automatically by the application
echo Step 5: Database migration will be handled automatically...
echo (No manual migration needed - the app handles this internally)
echo.

REM Check service status
echo Step 6: Checking service status...
%DOCKER_COMPOSE_CMD% ps
echo.

REM Wait for application
echo Step 7: Waiting for application to fully start - 10 seconds...
timeout /t 10 /nobreak >nul
echo.

echo ========================================
echo DEPLOYMENT COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Your application is now running:
echo Frontend: http://localhost
echo API: http://localhost/api
echo.
echo Management commands:
echo View logs: %DOCKER_COMPOSE_CMD% logs -f
echo Stop services: %DOCKER_COMPOSE_CMD% down
echo Restart services: %DOCKER_COMPOSE_CMD% restart
echo.
echo Account notice:
echo Please register a new account via the UI or API (/api/auth/register) before login.
echo.
echo Press any key to exit...
pause >nul