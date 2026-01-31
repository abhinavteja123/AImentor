@echo off
echo.
echo ================================================
echo   Hot Reload Setup Verification
echo ================================================
echo.

echo [1/4] Checking Docker Compose configuration...
docker compose config > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✓ docker-compose.yml is valid
) else (
    echo   ✗ docker-compose.yml has errors
    exit /b 1
)

echo.
echo [2/4] Checking frontend configuration...
findstr /C:"CHOKIDAR_USEPOLLING" docker-compose.yml > nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Frontend polling enabled
) else (
    echo   ✗ Frontend polling not found
)

findstr /C:"npm run dev" frontend\Dockerfile > nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Frontend dev command configured
) else (
    echo   ✗ Frontend dev command not found
)

echo.
echo [3/4] Checking backend configuration...
findstr /C:"--reload" docker-compose.yml > nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Backend reload enabled
) else (
    echo   ✗ Backend reload not found
)

findstr /C:"./backend:/app" docker-compose.yml > nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Backend bind mount configured
) else (
    echo   ✗ Backend bind mount not found
)

echo.
echo [4/4] Checking volume mounts...
findstr /C:"/app/node_modules" docker-compose.yml > nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Frontend node_modules excluded
) else (
    echo   ✗ Frontend node_modules not excluded
)

findstr /C:"/app/__pycache__" docker-compose.yml > nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Backend cache excluded
) else (
    echo   ✗ Backend cache not excluded
)

echo.
echo ================================================
echo   Verification Complete!
echo ================================================
echo.
echo Next steps:
echo   1. docker compose down
echo   2. docker compose build
echo   3. docker compose up
echo.
echo See HOT-RELOAD-SETUP.md for full instructions.
echo.
