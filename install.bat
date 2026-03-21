@echo off
REM Agent-Core Installation Script for Windows
REM Installs Agent-Core from PyPI

setlocal enabledelayedexpansion

set VERSION=1.0.0
set REPO_URL=https://github.com/your-org/agent-core

echo.
echo ╔════════════════════════════════════════╗
echo ║     Agent-Core Installer v%VERSION%        ║
echo ╚════════════════════════════════════════╝
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found %PYTHON_VERSION%
echo.

REM Parse installation type
set INSTALL_TYPE=%1
if "%INSTALL_TYPE%"=="" set INSTALL_TYPE=pypi

echo Installing Agent-Core from PyPI...
pip install --upgrade pip setuptools wheel
pip install agent-core

if %errorlevel% neq 0 (
    echo Error: Installation failed
    pause
    exit /b 1
)

REM Handle optional dependencies
if "%INSTALL_TYPE%"=="redis" (
    echo Installing Redis support...
    pip install agent-core[redis]
) else if "%INSTALL_TYPE%"=="dev" (
    echo Installing development tools...
    pip install agent-core[dev]
) else if "%INSTALL_TYPE%"=="all" (
    echo Installing all optional dependencies...
    pip install agent-core[dev,redis]
)

REM Verify installation
echo.
echo Verifying installation...
python -c "import agent_core; print(f'Agent-Core {agent_core.__version__} installed')" >nul 2>&1
if errorlevel 1 (
    echo Error: Installation verification failed
    pause
    exit /b 1
)

echo Installation successful!
echo.
echo ╔════════════════════════════════════════╗
echo ║          Next Steps                    ║
echo ╚════════════════════════════════════════╝
echo.
echo 1. Check version:
echo    agent-core version
echo.
echo 2. Start the API server:
echo    agent-core start --host 0.0.0.0 --port 8000
echo.
echo 3. Retrieve tools (in another terminal):
echo    agent-core retrieve "edit a file" --top-k 5
echo.
echo 4. Visit API docs:
echo    http://localhost:8000/docs
echo.
echo Documentation: %REPO_URL%#readme
echo.

pause
