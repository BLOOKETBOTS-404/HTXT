@echo off
REM Simple batch wrapper to run HTXT converter
if "%1"=="" (
  echo Usage: %~n0 input.htxt [output.html]
  goto :eof
)
python "%~dp0htxt_converter.py" "%~dp0%1" %2
