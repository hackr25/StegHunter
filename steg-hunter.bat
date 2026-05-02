@echo off
REM StegHunter CLI Wrapper
REM Usage: steg-hunter.bat [command] [arguments]

python "%~dp0steg_hunter_cli.py" %*
