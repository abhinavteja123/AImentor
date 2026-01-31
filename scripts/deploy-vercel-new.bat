@echo off
setlocal enabledelayedexpansion

REM AI Mentor - Vercel Deployment Script (Windows)
REM This script deploys the application to Vercel with auto-deploy disabled

echo ========================================
echo AI Mentor - Vercel Deployment Script
echo ========================================
echo.

REM Check if Vercel CLI is installed
where vercel >nul 2>nul
if !errorlevel! neq 0 (
    echo [ERROR] Vercel CLI is not installed
    echo [INFO] Installing Vercel CLI globally...
    call npm install -g vercel
    if !errorlevel! neq 0 (
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
set AUTH_STATUS=!errorlevel!

if !AUTH_STATUS! neq 0 (
    echo [ERROR] Not logged in to Vercel
    echo [INFO] Please login to Vercel...
    echo.
    vercel login
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Login failed
        pause
        exit /b 1
    )
    echo.
    echo [OK] Login successful
) else (
    echo [OK] Already logged in to Vercel
)
echo.

REM Parse command line arguments
set SERVICE=%1
set DEPLOYMENT_TYPE=%2

if "!SERVICE!"=="" set SERVICE=all
if "!DEPLOYMENT_TYPE!"=="" set DEPLOYMENT_TYPE=production

echo [INFO] Deployment Configuration:
echo    - Service: !SERVICE!
echo    - Environment: !DEPLOYMENT_TYPE!
echo.

REM Confirm deployment
set /p CONFIRM="Do you want to proceed with deployment? (y/N): "
if /i not "!CONFIRM!"=="y" (
    echo [INFO] Deployment cancelled
    pause
    exit /b 0
)

echo.

REM Deploy Frontend
if /i "!SERVICE!"=="frontend" (
    goto deploy_frontend
)
if /i "!SERVICE!"=="backend" (
    goto deploy_backend
)
if /i "!SERVICE!"=="all" (
    goto deploy_all
)

echo [ERROR] Invalid service: !SERVICE!
echo [INFO] Valid options: frontend, backend, all
pause
exit /b 1

:deploy_all
echo [INFO] Deploying both Frontend and Backend...
echo.
call :deploy_frontend
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Frontend deployment failed
    pause
    exit /b 1
)
echo.
call :deploy_backend
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Backend deployment failed
    pause
    exit /b 1
)
goto success

:deploy_frontend
echo ========================================
echo Deploying Frontend (Next.js)
echo ========================================
cd frontend
if /i "!DEPLOYMENT_TYPE!"=="production" (
    echo [INFO] Deploying frontend to PRODUCTION...
    vercel --prod --yes --name ai-mentor-frontend
) else (
    echo [INFO] Deploying frontend to PREVIEW...
    vercel --yes --name ai-mentor-frontend
)
set FRONTEND_STATUS=!errorlevel!
cd ..
if !FRONTEND_STATUS! neq 0 (
    echo [ERROR] Frontend deployment failed with exit code: !FRONTEND_STATUS!
    exit /b 1
)
echo [OK] Frontend deployed successfully
exit /b 0

:deploy_backend
echo ========================================
echo Deploying Backend (FastAPI)
echo ========================================
cd backend
if /i "!DEPLOYMENT_TYPE!"=="production" (
    echo [INFO] Deploying backend to PRODUCTION...
    vercel --prod --yes --name ai-mentor-backend
) else (
    echo [INFO] Deploying backend to PREVIEW...
    vercel --yes --name ai-mentor-backend
)
set BACKEND_STATUS=!errorlevel!
cd ..
if !BACKEND_STATUS! neq 0 (
    echo [ERROR] Backend deployment failed with exit code: !BACKEND_STATUS!
    exit /b 1
)
echo [OK] Backend deployed successfully
exit /b 0

:success
echo.
echo ========================================
echo [OK] Deployment complete!
echo ========================================
echo.
echo Next Steps:
echo    1. Copy the deployment URLs from above
echo    2. Set NEXT_PUBLIC_API_URL in frontend to backend URL
echo    3. Run: scripts\setup-vercel-env.bat to configure environment variables
echo    4. Update CORS_ORIGINS in backend to include frontend URL
echo.
echo [WARNING] Auto-deploy on push is DISABLED in vercel.json
echo    To enable, go to: Vercel Dashboard -^> Project Settings -^> Git
echo.
pause
exit /b 0
