@echo off
REM One-click start backend + frontend (dev). Keeps window open for confirmation.
setlocal

REM Ensure working from script directory (handle UNC/long paths)
pushd "%~dp0"
set "ROOT=%CD%"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\ui"
set "PY=%ROOT%\.venv\Scripts\python.exe"

echo [INFO] Root: %ROOT%
echo [INFO] Backend: %BACKEND%
echo [INFO] Frontend: %FRONTEND%

echo.
if not exist "%PY%" (
  echo [ERROR] %PY% not found.
  echo Please run: python -m venv .venv ^& .\.venv\Scripts\pip install -r requirements.txt
  pause
  goto :end
)

echo [BACKEND] starting uvicorn on 8000...
start "backend" cmd /k "pushd ""%BACKEND%"" && ""%PY%"" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [FRONTEND] starting npm run dev on 5173...
start "frontend" cmd /k "pushd ""%FRONTEND%"" && if not exist node_modules npm install && npm run dev -- --host --port 5173"

echo.
echo Frontend: http://127.0.0.1:5173
echo Backend : http://127.0.0.1:8000
echo.
pause

:end
popd
endlocal
