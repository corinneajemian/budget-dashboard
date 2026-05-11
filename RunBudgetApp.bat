@echo off
cd /d "%~dp0"
echo =====================================
echo Installing required Python packages...
echo =====================================
py -m pip install -r requirements.txt
echo.
echo =====================================
echo Launching Budget App...
echo =====================================
py -m streamlit run BudgetApp.py
pause