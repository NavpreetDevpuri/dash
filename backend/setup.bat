@echo off
SETLOCAL

echo === Starting setup for Consumer Agents backend ===

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Is python installed?
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    exit /b 1
)
echo Virtual environment activated.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    exit /b 1
)
echo Dependencies installed successfully.

REM Create necessary directories
echo Creating necessary directories...
if not exist logs mkdir logs
if not exist instance mkdir instance
echo Directories created.

REM Set up .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    echo OPENAI_API_KEY=your-api-key-here > .env
    echo .env file created. Please edit it to add your API keys.
) else (
    echo .env file already exists.
)

echo === Setup complete! ===
echo To use the standalone test script without Celery:
echo python -m app.consumer_agents.test_consumer_standalone
echo To run the full application:
echo flask run
echo To run with Docker:
echo docker-compose up

ENDLOCAL 