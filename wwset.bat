@echo off
:: 设置控制台代码页为简体中文 GBK
chcp 936 >nul
setlocal EnableDelayedExpansion

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员权限运行此脚本
    pause
    exit /b 1
)

:: 创建系统级别的命令别名
set "INSTALL_DIR=%ProgramFiles%\WWSet"
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

:: 复制程序文件到安装目录
copy /Y "%~dp0wsl_command.py" "%INSTALL_DIR%\" >nul
copy /Y "%~0" "%INSTALL_DIR%\wwset.bat" >nul

:: 创建命令别名脚本
echo @echo off > "%INSTALL_DIR%\wwset.cmd"
echo python "%INSTALL_DIR%\wsl_command.py" %%* >> "%INSTALL_DIR%\wwset.cmd"

:: 将安装目录添加到系统 PATH
set "PATH_REG_QUERY=reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path"
for /f "tokens=2,*" %%A in ('%PATH_REG_QUERY%') do set "CURRENT_PATH=%%B"

echo !CURRENT_PATH! | findstr /C:"%INSTALL_DIR%" >nul
if %errorLevel% neq 0 (
    setx /M PATH "%CURRENT_PATH%;%INSTALL_DIR%"
)

:: ÿ̨Ϊ Consolas Ըõʾ
reg add "HKEY_CURRENT_USER\Console" /v "FaceName" /t REG_SZ /d "Consolas" /f >nul 2>&1

::  Python ǷѰװ
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo PythonδװزװPython...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

::  WSL Ƿ
wsl --status >nul 2>&1
if %errorLevel% neq 0 (
    echo  WSL...
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    echo  WSL װȻ...
    pause
    exit /b 1
)

:: Ƿװ WSL2
wsl --set-default-version 2 >nul 2>&1
if %errorLevel% neq 0 (
    echo  WSL2 ...
    curl -L -o wsl_update.msi https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
    msiexec /i wsl_update.msi /quiet
    del wsl_update.msi
    wsl --set-default-version 2
)

:: Ƿ Linux 
wsl -l >nul 2>&1
if %errorLevel% neq 0 (
    echo δ⵽ Linux ,ڰװ Ubuntu...
    wsl --install -d Ubuntu
)

:: Ҫ Python ģ
python -c "import subprocess" >nul 2>&1
if %errorLevel% neq 0 (
    echo ڰװҪ Python ģ...
    python -m pip install subprocess.run
)

:: ӵϵͳ PATH
echo ӵϵͳ PATH...
setx /M PATH "%CURRENT_PATH%;%INSTALL_DIR%"
goto :run_command

:update_program
echo ڸ³...
:: Ӹ߼°汾
:: ʱֻʾϢ
echo Ѹµ°汾
goto :run_command

:uninstall_program
echo  ж...
:: ϵͳ PATH Ƴ·
set "NEW_PATH=!CURRENT_PATH:%INSTALL_DIR%=!"
setx /M PATH "!NEW_PATH!"
echo  Ѵϵͳж
echo ֶɾ %INSTALL_DIR%
pause
exit /b 0

:run_command
:: 
python "%~dp0wsl_command.py" %*

endlocal 