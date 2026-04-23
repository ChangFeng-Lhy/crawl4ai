import winreg
import os
import subprocess

def get_installed_apps_with_locations():
    """
    获取Windows系统中已安装的应用程序列表及其安装位置
    返回: 包含(应用名称, 安装路径)的列表
    """
    apps = []
    
    # 定义需要检查的注册表路径
    registry_paths = [
        # 系统安装的64位程序
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        # 系统安装的32位程序（在64位系统上）
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        # 当前用户安装的程序
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hive, path in registry_paths:
        try:
            with winreg.OpenKey(hive, path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                # 获取应用名称
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                # 获取安装位置
                                location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                
                                # 确保两个值都存在且不为空
                                if name and location:
                                    apps.append((name, location))
                            except FileNotFoundError:
                                # 如果缺少DisplayName或InstallLocation，跳过此项
                                continue
                    except WindowsError:
                        continue
        except WindowsError:
            continue
    
    return apps

def start_chrome():
    installed_apps = get_installed_apps_with_locations()
    
    # print(f"找到 {len(installed_apps)} 个已安装应用：")
    for i, (name, location) in enumerate(installed_apps, 1):
        if name == "Google Chrome":
            # print(f"{name} (Google Chrome) {location}")
            chrome_exe = os.path.join(location, "chrome.exe")
            print(f"Chrome路径: {chrome_exe}")
            user_data_dir = os.path.join(os.getcwd(),"result")
            os.makedirs(user_data_dir, exist_ok=True)
            port = 9222
            cmd = [
                chrome_exe,
                f"--remote-debugging-port={port}",
                f'--user-data-dir={user_data_dir}',
            ]
            try:
                # 启动Chrome
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                print(f"Chrome已启动，进程ID: {process.pid}")
                print(f"远程调试地址: http://localhost:{port}")
                
                # return process
            except Exception as e:
                print(f"启动Chrome失败: {e}")
                # return None


# # 使用示例
if __name__ == "__main__":
    start_chrome()