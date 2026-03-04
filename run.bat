@echo off
REM GreenRoute - Quick Start Script for Windows

echo ========================================
echo   GreenRoute - CO2 Optimized Routing
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Check if dependencies are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Check if CO2 model exists
if not exist "co2_model.pkl" (
    echo WARNING: CO2 model not found!
    echo Please ensure co2_model.pkl is in the project root directory.
    echo.
    pause
    exit /b 1
)

REM Check if RL model exists
if not exist "rl_models\ppo_delivery_route.zip" (
    echo RL model not found!
    echo Please run: python rl/train_ppo.py
    echo Or continue without RL optimization (will use greedy fallback)
    echo.
    pause
)

REM Start the API server
echo ========================================
echo Starting GreenRoute API Server...
echo ========================================
echo.
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Open frontend/index.html in your browser to use the app
echo.
echo Press Ctrl+C to stop the server
echo.

python api/main.py
