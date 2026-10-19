@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
goto envready
:usepython
where python >nul 2>nul
if errorlevel 1 goto nopython
python -m venv .venv
:envready
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto failed
".venv\Scripts\python.exe" preprocessing.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" analysis_summary.py
if errorlevel 1 goto failed
echo.
echo SUCCESS. Your Week 2 output files are in the results folder.
pause
exit /b 0
:nopython
echo Install Python 3.10 or newer from python.org, enable Add Python to PATH, then retry.
pause
exit /b 1
:failed
echo A step failed. Read the error above. No submission has been sent.
pause
exit /b 1
