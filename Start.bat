@echo off

echo Starting API...
start cmd /k "cd Back && uvicorn main_API:app --reload"

timeout /t 2

echo Starting Detector...
start cmd /k "cd Back && python main.py"

timeout /t 2

echo Starting Frontend...
start cmd /k "cd Front && npm start"

pause