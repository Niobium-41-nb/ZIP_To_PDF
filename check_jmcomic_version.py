#!/usr/bin/env python3
"""
检查 JMComic 版本
"""
try:
    import jmcomic
    print(f"✅ JMComic 版本: {jmcomic.__version__}")
    
    # 测试基本功能
    from jmcomic import JmOption, JmDownloader
    option = JmOption.default()
    print("✅ JMComic 基本功能正常")
    
except ImportError as e:
    print(f"❌ JMComic 导入失败: {e}")
except Exception as e:
    print(f"❌ JMComic 测试失败: {e}")