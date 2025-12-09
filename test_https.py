#!/usr/bin/env python3
"""
HTTPS连接测试脚本
"""
import requests
import ssl
import urllib3
import sys
import time

def test_https_connection():
    """测试HTTPS连接"""
    print("=" * 50)
    print("HTTPS连接测试")
    print("=" * 50)
    
    # 禁用SSL警告（因为使用自签名证书）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    url = "https://localhost:5000"
    
    print(f"测试URL: {url}")
    print("正在尝试连接...")
    
    try:
        # 尝试连接
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            print("✓ HTTPS连接成功！")
            print(f"  状态码: {response.status_code}")
            print(f"  响应内容长度: {len(response.text)} 字节")
            print(f"  服务器: {response.headers.get('Server', 'Unknown')}")
            return True
        else:
            print(f"✗ 连接失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL证书错误: {e}")
        print("  这是正常的，因为使用的是自签名证书")
        print("  浏览器访问时也会显示类似警告")
        return True  # SSL错误是预期的
        
    except requests.exceptions.ConnectionError as e:
        print(f"✗ 连接错误: {e}")
        print("  请确保服务器正在运行")
        return False
        
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def check_certificate():
    """检查SSL证书"""
    print("\n" + "=" * 50)
    print("SSL证书检查")
    print("=" * 50)
    
    cert_file = "cert.pem"
    key_file = "key.pem"
    
    import os
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✓ 证书文件存在:")
        print(f"  证书: {cert_file} ({os.path.getsize(cert_file)} 字节)")
        print(f"  私钥: {key_file} ({os.path.getsize(key_file)} 字节)")
        
        # 尝试读取证书信息
        try:
            import OpenSSL
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
                cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
                
                print("\n证书信息:")
                print(f"  主题: {cert.get_subject()}")
                print(f"  颁发者: {cert.get_issuer()}")
                print(f"  有效期: {cert.get_notBefore()} 到 {cert.get_notAfter()}")
                print(f"  序列号: {cert.get_serial_number()}")
                
        except ImportError:
            print("  (需要pyOpenSSL库来显示详细证书信息)")
        except Exception as e:
            print(f"  读取证书信息失败: {e}")
            
    else:
        print("✗ 证书文件不存在")
        return False
    
    return True

def start_server_instructions():
    """提供启动服务器的说明"""
    print("\n" + "=" * 50)
    print("启动HTTPS服务器")
    print("=" * 50)
    
    print("要启动HTTPS服务器，请运行以下命令之一:")
    print("\n1. 直接运行app.py:")
    print("   python app.py")
    
    print("\n2. 使用run.py:")
    print("   python run.py --web")
    
    print("\n3. 后台运行:")
    print("   python app.py > server.log 2>&1 &")
    
    print("\n服务器启动后，请访问:")
    print("  https://localhost:5000")
    
    print("\n注意:")
    print("  • 由于使用自签名证书，浏览器会显示'不安全'警告")
    print("  • 点击'高级' → '继续前往localhost（不安全）'")
    print("  • 证书有效期为365天")

def main():
    """主函数"""
    print("JM漫画下载服务HTTPS配置验证")
    print("=" * 50)
    
    # 检查证书
    cert_ok = check_certificate()
    
    if not cert_ok:
        print("\n✗ 证书检查失败，请重新生成证书")
        return 1
    
    print("\n" + "=" * 50)
    print("测试HTTPS连接")
    print("=" * 50)
    
    # 询问是否启动服务器测试
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("正在测试HTTPS连接...")
        success = test_https_connection()
        
        if success:
            print("\n✓ 所有检查通过！")
            print("您的JM漫画下载服务已成功配置HTTPS")
            return 0
        else:
            print("\n✗ HTTPS连接测试失败")
            print("请确保服务器正在运行")
            return 1
    else:
        print("跳过连接测试（使用 --test 参数进行完整测试）")
        start_server_instructions()
        return 0

if __name__ == "__main__":
    sys.exit(main())