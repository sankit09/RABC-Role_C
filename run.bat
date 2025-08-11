# run_dashboard.bat (Windows)

@echo off

REM Activate virtual environment
call venv\Scripts\activate

REM Check if .env exists
if not exist .env (
    echo Please create .env file with your Azure OpenAI credentials
    exit /b 1
)

REM Start FastAPI in new window
echo Starting FastAPI backend...
start cmd /k "uvicorn app.main:app --reload --port 8000"

REM Wait for FastAPI to start
timeout /t 5

REM Start Streamlit
echo Starting Streamlit dashboard...
streamlit run streamlit_app.py --server.port 8501
