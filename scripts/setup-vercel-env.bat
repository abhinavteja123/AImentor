@echo off
REM AI Mentor - Vercel Environment Variables Setup Script (Windows)
REM This script helps you set up environment variables for Vercel deployment

echo ========================================
echo AI Mentor - Vercel Environment Setup
echo ========================================
echo.

REM Check if Vercel CLI is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Vercel CLI is not installed
    echo Please run: npm install -g vercel
    pause
    exit /b 1
)

REM Check if user is logged in
vercel whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Not logged in to Vercel
    echo Please run: vercel login
    pause
    exit /b 1
)

REM Parse environment argument
set ENV=%1
if "%ENV%"=="" set ENV=production

echo [INFO] Setting up environment variables for: %ENV%
echo.
echo [WARNING] You'll need the following information:
echo    - PostgreSQL Database URL
echo    - MongoDB URL
echo    - Redis URL
echo    - Google API Key (Gemini)
echo    - JWT Secret Key
echo.

set /p CONFIRM="Do you want to continue? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo [INFO] Setup cancelled
    pause
    exit /b 0
)

echo.
echo [INFO] Setting environment variables...
echo.

REM Helper function to set environment variable
call :SetEnvVar "DATABASE_URL" "PostgreSQL URL (e.g., postgresql://user:pass@host:5432/db)"
call :SetEnvVar "MONGODB_URL" "MongoDB URL (e.g., mongodb://host:27017 or MongoDB Atlas)"
call :SetEnvVar "MONGODB_DB" "MongoDB Database Name (e.g., ai_mentor)"
call :SetEnvVar "REDIS_URL" "Redis URL (e.g., redis://host:6379 or Upstash Redis)"
call :SetEnvVar "GOOGLE_API_KEY" "Google Gemini API Key"
call :SetEnvVar "JWT_SECRET_KEY" "JWT Secret Key (generate a strong random string)"
call :SetEnvVar "CORS_ORIGINS" "CORS Origins (e.g., https://yourdomain.com)"
call :SetEnvVar "NEXT_PUBLIC_API_URL" "Public API URL (e.g., https://your-project.vercel.app)"

echo.
echo ========================================
echo [OK] Environment setup complete!
echo ========================================
echo.
echo Next Steps:
echo    1. Verify variables in Vercel Dashboard
echo    2. Deploy your application: npm run vercel:deploy
echo    3. Test the deployment
echo.
pause
exit /b 0

:SetEnvVar
set VAR_NAME=%~1
set VAR_PROMPT=%~2

echo [INPUT] %VAR_PROMPT%
set /p VAR_VALUE="   Value: "

if not "%VAR_VALUE%"=="" (
    echo %VAR_VALUE% | vercel env add %VAR_NAME% %ENV% >nul 2>nul
    if %errorlevel% equ 0 (
        echo    [OK] %VAR_NAME% set
    ) else (
        echo    [WARNING] Failed to set %VAR_NAME%
    )
) else (
    echo    [WARNING] Skipped %VAR_NAME%
)
echo.
exit /b 0
