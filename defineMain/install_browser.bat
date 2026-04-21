@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Crawl4AI Browser Installer
echo ========================================
echo.

:: Check admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Administrator rights required
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Step 1: Check Python
echo [1/2] Checking Python environment...
echo.

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Found Python: !PYTHON_VERSION!
    
    echo !PYTHON_VERSION! | findstr /C:"Python 3.12" >nul
    if errorlevel 1 (
        echo [WARN] Python version is not 3.12.x
        echo Will install Python 3.12.8 for compatibility
        goto INSTALL_PYTHON
    ) else (
        echo [OK] Python version is compatible
        goto CHECK_PLAYWRIGHT
    )
) else (
    echo [INFO] Python not found
    echo Will install Python 3.12.8
    goto INSTALL_PYTHON
)

:INSTALL_PYTHON
echo.
echo [INFO] Downloading Python 3.12.8 (~50MB)...
echo This may take a few minutes depending on your network speed.
echo.

set DOWNLOAD_DIR=%TEMP%\crawl4ai_install
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

set PYTHON_INSTALLER=%DOWNLOAD_DIR%\python-3.12.8-amd64.exe

:: Try multiple download sources with progress bar
echo Trying official source...
powershell -Command "$ProgressPreference = 'Continue'; $wc = New-Object System.Net.WebClient; $wc.DownloadFile('https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe', '%PYTHON_INSTALLER%')" 2>nul

if not exist "%PYTHON_INSTALLER%" (
    echo Official source failed, trying Tsinghua mirror...
    powershell -Command "$ProgressPreference = 'Continue'; $wc = New-Object System.Net.WebClient; $wc.DownloadFile('https://mirrors.tuna.tsinghua.edu.cn/python/3.12.8/python-3.12.8-amd64.exe', '%PYTHON_INSTALLER%')" 2>nul
)

if not exist "%PYTHON_INSTALLER%" (
    echo [ERROR] Failed to download Python installer
    echo.
    echo Please download manually from:
    echo https://mirrors.tuna.tsinghua.edu.cn/python/3.12.8/python-3.12.8-amd64.exe
    echo Save to: %PYTHON_INSTALLER%
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Download complete
echo.
echo [INFO] Installing Python 3.12.8...
echo Installation is running in the background, please wait...
echo.

:: Install Python with passive mode (shows progress but no user interaction needed)
start "" /wait "%PYTHON_INSTALLER%" /passive InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0 TargetDir=C:\Python312

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python installation failed
    echo Exit code: %errorlevel%
    pause
    exit /b 1
)

echo.
echo [OK] Python 3.12.8 installed successfully
echo.

set PATH=C:\Python312;C:\Python312\Scripts;%PATH%

:: Install Playwright package
echo [INFO] Installing Playwright package...
pip install playwright 2>&1 | findstr /C:"Successfully installed" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Playwright package
    pause
    exit /b 1
)
echo [OK] Playwright package installed
echo.

goto INSTALL_BROWSER

:CHECK_PLAYWRIGHT
:: Check if playwright is already installed
echo.
echo [INFO] Checking Playwright installation...
python -m playwright --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Playwright is already installed
    goto INSTALL_BROWSER
) else (
    echo [INFO] Playwright not found, installing...
    pip install playwright 2>&1 | findstr /C:"Successfully installed" >nul
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Playwright package
        pause
        exit /b 1
    )
    echo [OK] Playwright package installed
    echo.
)

:INSTALL_BROWSER
:: Step 2: Install Playwright browser
echo [2/2] Installing Playwright Chromium browser (~300MB)...
echo This may take several minutes, please wait...
echo.

echo Starting Playwright browser installation...
echo Downloading Chromium browser files...
echo Progress will be shown below:
echo.

python -m playwright install chromium

if %errorlevel% neq 0 (
    echo.
    echo [WARN] First attempt failed, retrying with force...
    echo.
    echo Retrying installation...
    
    python -m playwright install --force chromium
    
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Browser installation failed!
        echo.
        echo Possible solutions:
        echo 1. Check your internet connection
        echo 2. Temporarily disable firewall/antivirus
        echo 3. Run manually: python -m playwright install chromium
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [OK] Playwright browser installed successfully
echo.

:: Verification
echo Verifying installation...
echo.

python -m playwright --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Playwright command available
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Installed components:
echo   - Python 3.12.8 ^(if needed^)
echo   - Playwright package
echo   - Playwright Chromium browser
echo.
echo Next steps:
echo   1. Copy .llm.env.example to .llm.env
echo   2. Edit .llm.env and add your API key
echo   3. Run crawl4ai_app.exe
echo.
echo Tips:
echo   - logs/ and result/ directories will be created automatically
echo   - Check logs/ directory for troubleshooting
echo.

:: Cleanup
if exist "%DOWNLOAD_DIR%" rmdir /s /q "%DOWNLOAD_DIR%"

pause