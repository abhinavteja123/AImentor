@echo off
REM AI Life Mentor - Quick Start Script for Windows

echo.
echo ========================================
echo   AI Life Mentor - Docker Quick Start
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env file has been configured
findstr /C:"your_deepseek_api_key_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING: You need to configure your DeepSeek API key!
    echo.
    echo Please edit the .env file and replace:
    echo   DEEPSEEK_API_KEY=your_deepseek_api_key_here
    echo with your actual API key from https://platform.deepseek.com/
    echo.
    set /p CONTINUE="Do you want to continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
)

echo.
echo Step 1: Building Docker images...
echo.
docker-compose build

if %errorlevel% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Starting all services...
echo.
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)

echo.
echo Step 3: Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo   All services are running!
echo ========================================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   PostgreSQL: localhost:5432
echo   MongoDB:    localhost:27017
echo   Redis:      localhost:6379
echo.
echo To view logs:     docker-compose logs -f
echo To stop:          docker-compose down
echo To seed database: docker-compose exec backend python -m scripts.seed_database
echo.
pause
