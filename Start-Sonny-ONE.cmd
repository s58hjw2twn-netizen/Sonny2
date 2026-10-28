@echo off
setlocal
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 is needed. Install Python from python.org, then reopen this file.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" scripts\start_sonny_one_pilot.py
if errorlevel 1 goto failed
exit /b 0
:failed
 echo Sonny ONE could not start. Read the error above. No public deployment was made.
 pause
 exit /b 1
