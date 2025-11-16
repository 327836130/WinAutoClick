@echo off
REM WinAutoClick helper
REM Requires Python3.12, Node.js, PyInstaller (optional), npm
setlocal

REM Default: double-click runs dev (backend+frontend). CLI still supports build/dev.
if "%1"=="" goto dev
if /I "%1"=="dev" goto dev
if /I "%1"=="build" goto build
goto usage

:dev
echo [DEV] starting backend and frontend (two windows)...
start "backend" cmd /c "cd /d %~dp0..\backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "frontend" cmd /c "cd /d %~dp0..\ui && npm install && npm run dev -- --host --port 5173"
echo backend: http://127.0.0.1:8000  frontend: http://127.0.0.1:5173
goto end

:build
echo [BUILD] install backend deps...
python -m pip install -r ..\requirements.txt

echo [BUILD] build frontend...
pushd ..\ui
npm install
npm run build
popd

echo [BUILD] copy frontend dist -> frontend/ ...
if exist ..\frontend rmdir /S /Q ..\frontend
xcopy ..\ui\dist ..\frontend /E /I /Y

echo [BUILD] pyinstaller backend (single exe)...
pushd ..
pyinstaller --onefile --name AutoClickFramework backend\run_app.py
popd

echo Done. exe at dist\AutoClickFramework.exe
goto end

:usage
echo Usage:
echo   build.bat dev    ^> start backend+frontend (dev)
echo   build.bat build  ^> build frontend and pyinstaller backend

:end
endlocal
