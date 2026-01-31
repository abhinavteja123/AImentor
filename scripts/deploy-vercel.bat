@echo off
REM AI Mentor - Vercel Deployment Script (Windows)
REM This script deploys the application to Vercel with auto-deploy disabled

echo ========================================
echo AI Mentor - Vercel Deployment Script
echo ========================================
echo.

REM Check if Vercel CLI is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Vercel CLI is not installed
    echo [INFO] Installing Vercel CLI globally...
    call npm install -g vercel
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Vercel CLI
        pause
        exit /b 1
    )
)

echo [OK] Vercel CLI is installed
echo.

REM Check if user is logged in
echo [INFO] Checking Vercel authentication...
vercel whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Not logged in to Vercel
    echo [INFO] Please login to Vercel...
    call vercel login
    if %errorlevel% neq 0 (
        echo [ERROR] Login failed
        pause
        exit /b 1
    )
) else (
    echo [OK] Already logged in to Vercel
)
echo.

REM Parse command line arguments
set DEPLOYMENT_TYPE=%1
set PROJECT_NAME=%2

if "%DEPLOYMENT_TYPE%"=="" set DEPLOYMENT_TYPE=production
if "%PROJECT_NAME%"=="" set PROJECT_NAME=ai-life-mentor

echo [INFO] Deployment Configuration:
echo    - Environment: %DEPLOYMENT_TYPE%
echo    - Project Name: %PROJECT_NAME%
echo.

REM Confirm deployment
set /p CONFIRM="Do you want to proceed with deployment? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo [INFO] Deployment cancelled
    pause
    exit /b 0
)

echo.
REM Deploy based on type
if /i "%DEPLOYMENT_TYPE%"=="production" (
    echo [INFO] Deploying to PRODUCTION...
    call vercel --prod --yes --name "%PROJECT_NAME%"
) else (
    echo [INFO] Deploying to PREVIEW...
    call vercel --yes --name "%PROJECT_NAME%"
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Deployment failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo [OK] Deployment complete!
echo ========================================
echo.
echo Next Steps:
echo    1. Verify deployment at the provided URL
echo    2. Set up environment variables: npm run vercel:env
echo    3. Configure database connections
echo.
echo [WARNING] Auto-deploy on push is DISABLED by default in vercel.json
echo    To enable it, go to Vercel Dashboard -^> Project Settings -^> Git
echo.
pause
