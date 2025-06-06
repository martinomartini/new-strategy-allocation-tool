@echo off
echo 🏢 Starting Office Room & Oasis Booking System
echo ===============================================
echo.

echo Checking dependencies...
python -c "import streamlit, psycopg2, pandas; print('✅ All dependencies available')"
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo 🚀 Starting application...
echo 📍 Access at: http://localhost:8501
echo 🔑 Admin password: Set in secrets or use default
echo.

streamlit run app.py
