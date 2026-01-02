#!/usr/bin/env python3
"""
检查 JMComic 版本
"""
import sys

# 设置编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import jmcomic
    print(f"[OK] JMComic 版本: {jmcomic.__version__}")
    
    # 测试基本功能
    from jmcomic import JmOption, JmDownloader
    option = JmOption.default()
    print("[OK] JMComic 基本功能正常")
    
except ImportError as e:
    print(f"[ERROR] JMComic 导入失败: {e}")
except Exception as e:
    print(f"[ERROR] JMComic 测试失败: {e}")