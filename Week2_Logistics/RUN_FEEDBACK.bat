@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run RUN_WEEK2.bat first to prepare the environment.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" feedback_analysis.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto failed
echo SUCCESS: supplementary evidence regenerated and 16 tests passed.
pause
exit /b 0
:failed
echo Read the error above. No submission has been sent.
pause
exit /b 1
