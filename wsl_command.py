import sys
import subprocess
import locale
import json
import os

# 设置默认编码为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wwset_config.json')

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"default_distro": None}

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {str(e)}", file=sys.stderr)

def get_wsl_distros():
    """获取已安装的 WSL 发行版列表"""
    try:
        # 使用二进制模式运行命令
        result = subprocess.run(['wsl', '--list'], 
                              capture_output=True,
                              check=False)
        
        if result.returncode == 0:
            # 尝试多种编码方式解码输出
            encodings = ['utf-8', 'gbk', 'cp936', 'ascii']
            output = None
            
            for encoding in encodings:
                try:
                    output = result.stdout.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if output is None:
                print("错误: 无法解码WSL输出")
                return []
            
            distros = []
            for line in output.splitlines():
                # 跳过标题行
                if 'NAME' in line or 'Windows Subsystem for Linux' in line:
                    continue
                
                # 处理每一行
                line = line.strip()
                if line:
                    # 提取发行版名称（通常是第一列）
                    distro_name = line.split()[0].strip()
                    if distro_name and not distro_name.isspace():
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
    
    # 调试信息
    print("已安装的子系统:")
    for d in distros:
        print(f"  - '{d}'")
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
    save_config(config)
    print(f"已将 {actual_name} 设置为默认子系统")
    return True

def run_wsl_command(distro_name, command):
    try:
        # 构建完整的WSL命令
        wsl_command = f'wsl -d {distro_name} {command}'
        
        # 使用二进制模式执行命令
        result = subprocess.run(wsl_command, 
                              shell=True, 
                              capture_output=True)
        
        # 尝试解码输出
        encodings = ['utf-8', 'gbk', 'cp936', 'ascii']
        
        # 处理标准输出
        if result.stdout:
            for encoding in encodings:
                try:
                    output = result.stdout.decode(encoding)
                    print(output, end='')
                    break
                except UnicodeDecodeError:
                    continue
        
        # 处理错误输出
        if result.stderr:
            for encoding in encodings:
                try:
                    error = result.stderr.decode(encoding)
                    print("错误:", error, file=sys.stderr, end='')
                    break
                except UnicodeDecodeError:
                    continue
            
        return result.returncode
        
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