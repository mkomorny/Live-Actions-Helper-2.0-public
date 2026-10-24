@echo off
rem Runs the WebView2 shell (app\shell.py) as the isolated "redesign" instance beside the main Tk app:
rem own mutex, own %APPDATA%\Live Actions-redesign\settings.json, own UDP ports.
set LIVE_ACTIONS_INSTANCE=redesign
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
  start "" pyw -3 "%~dp0app\shell.py"
  goto :end
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "%~dp0app\shell.py"
  goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
  start "" py -3 "%~dp0app\shell.py"
  goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
  start "" python "%~dp0app\shell.py"
  goto :end
)
echo Python 3 is required to open Live Actions.
echo Install Python from python.org and tick "Add python.exe to PATH".
pause
:end
