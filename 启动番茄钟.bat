@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_LAUNCHER="
set "PYTHON_ARGS="

rem 优先使用 pyw，无控制台窗口；先用 py 确认解释器真实可用。
where pyw >nul 2>nul
if errorlevel 1 goto :try_py
py -3 -c "import platform; print(platform.python_version())" >nul 2>nul
if errorlevel 1 goto :try_py
set "PYTHON_LAUNCHER=pyw"
set "PYTHON_ARGS=-3"
goto :launch

:try_py
for /f "delims=" %%v in ('py -3 -c "import platform; print(platform.python_version())" 2^>nul') do (
    set "PYTHON_LAUNCHER=py"
)
if not defined PYTHON_LAUNCHER goto :try_python
set "PYTHON_ARGS=-3"
where pyw >nul 2>nul
if not errorlevel 1 set "PYTHON_LAUNCHER=pyw"
goto :launch

:try_python
for /f "delims=" %%v in ('python -c "import platform; print(platform.python_version())" 2^>nul') do (
    set "PYTHON_LAUNCHER=python"
)
if not defined PYTHON_LAUNCHER goto :try_workbuddy
set "PYTHON_ARGS="
where pythonw >nul 2>nul
if not errorlevel 1 set "PYTHON_LAUNCHER=pythonw"
goto :launch

:try_workbuddy
for /d %%D in ("%USERPROFILE%\.workbuddy\binaries\python\versions\*") do (
    if exist "%%D\python.exe" (
        if exist "%%D\pythonw.exe" (
            set "PYTHON_LAUNCHER=%%D\pythonw.exe"
        ) else (
            set "PYTHON_LAUNCHER=%%D\python.exe"
        )
    )
)
if not defined PYTHON_LAUNCHER goto :no_python
set "PYTHON_ARGS="
goto :launch

:launch
rem start 会在新进程中运行番茄钟，批处理程序随即退出并关闭自身窗口。
start "" /D "%~dp0" "%PYTHON_LAUNCHER%" %PYTHON_ARGS% main.py
exit /b 0

:no_python
echo.
echo 启动失败：未找到可用的 Python 3 解释器。
echo 请安装 Python 3.10 及以上版本，并确认包含 tkinter。
pause
exit /b 1
