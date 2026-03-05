@echo off
setlocal

set IMAGE=thanglong2807/be-cenvi:latest
set CONTAINER=cenvi_backend

if "%~1"=="" (
  set APP_DIR=%cd%
) else (
  set APP_DIR=%~1
)

echo [1/5] Pull image %IMAGE%
docker pull %IMAGE%
if errorlevel 1 goto :err

echo [2/5] Stop old container (if exists)
docker rm -f %CONTAINER% >nul 2>nul

echo [3/5] Ensure required folders
if not exist "%APP_DIR%\credentials" mkdir "%APP_DIR%\credentials"
if not exist "%APP_DIR%\app\data" mkdir "%APP_DIR%\app\data"

echo [4/5] Run container
docker run -d --name %CONTAINER% -p 8100:8100 --env-file "%APP_DIR%\.env" -e DOCKER=true -v "%APP_DIR%\credentials:/app/credentials:ro" -v "%APP_DIR%\app\data:/app/app/data" -v "%APP_DIR%\cenvi_audit.db:/app/cenvi_audit.db" %IMAGE%
if errorlevel 1 goto :err

echo [5/5] Show logs
docker logs --tail 100 %CONTAINER%
echo.
echo Deploy completed.
exit /b 0

:err
echo.
echo Deploy failed. Check output above.
exit /b 1