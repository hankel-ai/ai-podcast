@echo off
echo Registering AIPodcast Daily scheduled task...

schtasks /create /tn "AIPodcast Daily" ^
  /tr "pythonw \"%~dp0main.py\"" ^
  /sc daily /st 09:30 ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel% equ 0 (
    echo Task registered successfully! Will run daily at 09:30.
    echo.
    echo To verify: schtasks /query /tn "AIPodcast Daily"
    echo To delete:  schtasks /delete /tn "AIPodcast Daily" /f
) else (
    echo Failed to register task. Try running as Administrator.
)
pause
