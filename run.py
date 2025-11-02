#!/usr/bin/env python3
"""
Flask压缩包转PDF工具 - 启动脚本
"""

import os
import sys
import webbrowser
import threading
import time
from utils.file_utils import FileUtils

def check_dependencies():
    """检查必要的依赖包"""
    required_packages = [
        'flask',
        'pillow',
        'img2pdf', 
        'python-magic',
        'rarfile',
        'py7zr'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少必要的依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def open_browser():
    """在浏览器中打开应用"""
    time.sleep(2)  # 等待应用启动
    webbrowser.open('http://localhost:5000')

def main():
    """主函数"""
    print("=" * 50)
    print("Flask压缩包转PDF工具")
    print("=" * 50)
    
    # 检查依赖
    print("检查依赖包...")
    if not check_dependencies():
        sys.exit(1)
    
    # 创建必要目录
    print("创建项目目录...")
    FileUtils.create_directories()
    
    # 导入并启动Flask应用
    try:
        from app import app
        
        print("启动Flask应用...")
        print("应用地址: http://localhost:5000")
        print("按 Ctrl+C 停止应用")
        print("-" * 50)
        
        # 在浏览器中打开应用
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动Flask应用
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()