# run.bat (for Windows)
"""
@echo off

REM Activate virtual environment
call venv\Scripts\activate

REM Check if .env exists
if not exist .env (
    echo Creating .env file from .env.example
    copy .env.example .env
    echo Please edit .env with your Azure OpenAI credentials
    exit /b 1
)

REM Create data directories
if not exist data\input mkdir data\input
if not exist data\output mkdir data\output

REM Run the application
uvicorn app.main:app --reload --port 8000
"""