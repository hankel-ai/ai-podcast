@echo off
robocopy "%~dp0." "%USERPROFILE%\OneDrive\Programs\ai-podcast" /E /XD .git /PURGE /NFL /NDL /NJH /NJS
echo Deployed ai-podcast to Programs\ai-podcast
pause
