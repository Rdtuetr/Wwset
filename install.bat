@echo off
:: 设置代码页
chcp 65001 >nul

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员权限运行此安装程序
    pause
    exit /b 1
)

:: 设置安装目录
set "INSTALL_DIR=%SystemRoot%\System32"

:: 检查并安装 Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在下载 Python 安装程序...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile 'python_installer.exe'}"
    
    echo 正在安装 Python...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python_installer.exe
    
    :: 刷新环境变量
    call refreshenv.cmd
    if %errorLevel% neq 0 (
        echo 正在刷新环境变量...
        powershell -Command "& {$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')}"
    )
)

:: 创建命令文件
echo @echo off > "%INSTALL_DIR%\wwset.cmd"
echo set "PYTHONIOENCODING=utf-8" >> "%INSTALL_DIR%\wwset.cmd"
echo python "%INSTALL_DIR%\wsl_command.py" %%* >> "%INSTALL_DIR%\wwset.cmd"

:: 复制 Python 脚本到安装目录
copy /Y "%~dp0wsl_command.py" "%INSTALL_DIR%\" >nul

:: 检查 WSL 是否已启用
wsl --status >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在启用 WSL...
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    echo 请重启电脑以完成 WSL 安装，然后重新运行此脚本
    pause
    exit /b 1
)

:: 检查是否安装了 WSL2
wsl --set-default-version 2 >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在下载 WSL2 更新包...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi' -OutFile 'wsl_update.msi'}"
    
    echo 正在安装 WSL2...
    msiexec /i wsl_update.msi /quiet
    del wsl_update.msi
    wsl --set-default-version 2
)

:: 检查是否有 Linux 发行版
wsl -l >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在安装 Ubuntu...
    wsl --install -d Ubuntu
)

echo 安装完成！请重新打开命令提示符使用 wwset 命令
echo 示例：wwset Ubuntu ls
pause 