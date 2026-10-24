@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
  start "" pyw -3 "%~dp0app\helper.py"
  goto :end
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "%~dp0app\helper.py"
  goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
  start "" py -3 "%~dp0app\helper.py"
  goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
  start "" python "%~dp0app\helper.py"
  goto :end
)
echo Python 3 is required to open Live Actions.
echo Install Python from python.org and tick "Add python.exe to PATH".
pause
:end
