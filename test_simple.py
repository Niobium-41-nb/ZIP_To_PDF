#!/usr/bin/env python3
"""
简单功能测试脚本
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """测试基本功能"""
    print("测试Flask压缩包转PDF工具的基本功能...")
    
    try:
        # 测试导入
        from utils.file_utils import FileUtils
        from utils.compression import CompressionHandler
        from utils.image_processor import ImageProcessor
        from utils.pdf_generator import PDFGenerator
        
        print("✅ 所有核心模块导入成功")
        
        # 测试目录创建
        FileUtils.create_directories()
        print("✅ 目录创建成功")
        
        # 测试文件类型检测
        test_file = "test.jpg"
        file_type = FileUtils.get_file_type(test_file)
        print(f"✅ 文件类型检测: {test_file} -> {file_type}")
        
        # 测试自然排序
        test_files = ["file10.jpg", "file2.jpg", "file1.jpg"]
        sorted_files = sorted(test_files, key=FileUtils.natural_sort_key)
        print(f"✅ 自然排序测试: {sorted_files}")
        
        print("\n🎉 所有基本功能测试通过！")
        print("应用已准备就绪，可以运行 'python app.py' 启动服务")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_basic_functionality()