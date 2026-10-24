@echo off
rem Live Actions (WebView2 shell). The old Tk window is still available as "Launch Live Actions (classic Tk).bat".
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
