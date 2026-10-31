@echo off
REM One-time setup for APDIS on Windows. Double-click or run from the project folder.
cd /d "%~dp0"

echo [1/5] Creating virtual environment (.venv)...
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv
) else (
    python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
    echo Could not create the virtual environment. Is Python 3.12 installed and on PATH?
    pause
    exit /b 1
)

echo [2/5] Installing libraries (first time takes several minutes)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo Install failed. & pause & exit /b 1)

echo [3/5] Creating .env ...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo     Created .env - open it and paste your GEMINI_API_KEY.
) else (
    echo     .env already exists - left unchanged.
)

echo [4/5] Checking documents...
if exist "data\raw\documents\*.pdf" (
    echo     PDFs found in data\raw\documents - using them.
) else (
    echo     No PDFs found - creating sample documents.
    ".venv\Scripts\python.exe" scripts\make_sample_docs.py
)

echo [5/5] Building the vector database (downloads the embedding model the first time)...
".venv\Scripts\python.exe" scripts\ingest.py

echo.
echo Setup complete. Next:
echo   1. Put your Gemini API key in .env
echo   2. Double-click run_app.bat
pause
