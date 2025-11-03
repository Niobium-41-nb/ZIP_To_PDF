#!/usr/bin/env python3
"""
测试 GitHub Action 环境
"""
import os
import sys

def test_environment():
    """测试环境设置"""
    print("🧪 测试 GitHub Action 环境...")
    
    # 检查目录
    directories = ['uploads', 'temp', 'outputs', 'download']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    # 检查Python包
    try:
        import jmcomic
        print("✅ jmcomic 可用")
    except ImportError:
        print("❌ jmcomic 不可用")
        return False
    
    try:
        from app import app
        print("✅ Flask app 可用")
    except ImportError as e:
        print(f"❌ Flask app 导入失败: {e}")
        return False
    
    print("🎉 环境测试通过!")
    return True

if __name__ == '__main__':
    if test_environment():
        sys.exit(0)
    else:
        sys.exit(1)