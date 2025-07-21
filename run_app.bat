@echo off
call conda activate py
start /b python app.py
start http://127.0.0.1:5001
pause