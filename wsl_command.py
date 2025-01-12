import sys
import subprocess
import locale
import json
import os

# 设置默认编码为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 修改配置文件路径到用户目录
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.wwset')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

def load_config():
    """加载配置文件"""
    try:
        # 确保配置目录存在
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {str(e)}", file=sys.stderr)
    return {"default_distro": None}

def save_config(config):
    """保存配置文件"""
    try:
        # 确保配置目录存在
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {str(e)}", file=sys.stderr)
        return False
    return True

def get_wsl_distros():
    """获取已安装的 WSL 发行版列表"""
    try:
        # 使用 --list 而不是 --verbose，以获得更简单的输出
        result = subprocess.run(['wsl', '--list'], 
                              capture_output=True,
                              check=False)
        
        if result.returncode == 0:
            # 首先尝试 UTF-16LE（Windows 默认编码）
            try:
                output = result.stdout.decode('utf-16le')
            except UnicodeDecodeError:
                # 如果失败，尝试其他编码
                for encoding in ['utf-8', 'gbk', 'cp936']:
                    try:
                        output = result.stdout.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print("错误: 无法解码WSL输出")
                    return []
            
            distros = []
            for line in output.splitlines():
                line = line.strip()
                # 跳过空行和标题行
                if not line or '适用于 Linux 的 Windows 子系统分发版:' in line:
                    continue
                
                # 提取发行版名称，处理可能的 (默认) 标记
                distro_name = line.split('(默认)')[0].strip()
                if distro_name:
                    distros.append(distro_name)
            
            return distros
        return []
    except Exception as e:
        print(f"获取 WSL 发行版列表失败: {str(e)}", file=sys.stderr)
        return []

def set_default_distro(distro_name):
    """设置默认子系统"""
    # 获取可用的发行版列表
    distros = get_wsl_distros()
    
    # 如果列表为空，显示错误
    if not distros:
        print("错误: 未检测到已安装的 WSL 发行版")
        return False
    
    # 调试信息
    print("已安装的子系统:")
    for d in distros:
        print(f"  - {d}")
    print(f"尝试设置的子系统: '{distro_name}'")
    
    # 检查子系统是否存在（不区分大小写）
    if not any(d.lower() == distro_name.lower() for d in distros):
        print(f"错误: 未找到子系统 '{distro_name}'")
        print("可用的子系统:")
        for d in distros:
            print(f"  - {d}")
        return False
    
    # 使用匹配到的实际名称（保持原始大小写）
    actual_name = next(d for d in distros if d.lower() == distro_name.lower())
    
    config = load_config()
    config["default_distro"] = actual_name
    if save_config(config):
        print(f"已将 {actual_name} 设置为默认子系统")
        return True
    else:
        print("错误: 无法保存配置")
        return False

def run_wsl_command(distro_name, command):
    try:
        # 构建完整的WSL命令，添加 NODE_NO_WARNINGS=1 来禁用警告
        wsl_command = f'wsl -d {distro_name} bash -ic "export NODE_NO_WARNINGS=1; {command}"'
        
        # 使用 Popen 实时获取输出
        process = subprocess.Popen(
            wsl_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8'
        )

        # 实时处理输出
        while True:
            # 读取标准输出
            output = process.stdout.readline()
            if output:
                # 过滤掉不需要的警告信息
                if not any(msg in output for msg in [
                    'DeprecationWarning',
                    'trace-deprecation'
                ]):
                    print(output.rstrip())
            
            # 读取错误输出
            error = process.stderr.readline()
            if error:
                # 过滤掉特定错误和警告
                if not any(msg in error for msg in [
                    'bash: 无法设置终端进程组',
                    'bash: no job control in this shell',
                    'DeprecationWarning',
                    'trace-deprecation'
                ]):
                    print("错误:", error.rstrip(), file=sys.stderr)
            
            # 检查进程是否结束
            if output == '' and error == '' and process.poll() is not None:
                break
        
        return process.returncode
        
    except Exception as e:
        print(f"执行出错: {str(e)}", file=sys.stderr)
        return 1

def show_usage():
    """显示使用说明"""
    print("用法:")
    print("  wwset <子系统名> <命令>     在指定子系统中执行命令")
    print("  wwset set <子系统名>        设置默认子系统")
    print("  wwset <命令>                在默认子系统中执行命令")
    return 1

def main():
    args = sys.argv[1:]
    if not args:
        return show_usage()
    
    # 处理设置默认子系统的命令
    if args[0] == 'set':
        if len(args) != 2:
            print("错误: 设置默认子系统需要指定子系统名")
            return 1
        return 0 if set_default_distro(args[1]) else 1
    
    config = load_config()
    if len(args) == 1:
        # 单个参数时使用默认子系统
        if not config["default_distro"]:
            print("错误: 未设置默认子系统，请先使用 'wwset set <子系统名>' 设置")
            return 1
        return run_wsl_command(config["default_distro"], args[0])
    else:
        # 多个参数时第一个是子系统名
        return run_wsl_command(args[0], ' '.join(args[1:]))

if __name__ == "__main__":
    sys.exit(main()) 