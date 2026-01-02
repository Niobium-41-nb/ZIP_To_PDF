#!/usr/bin/env python3
"""
安全证书生成脚本
在运行时生成自签名SSL证书，不提交到Git
"""

import os
import subprocess
import sys

def generate_ssl_certificates():
    """生成自签名SSL证书"""
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    # 检查证书是否已存在
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"SSL证书已存在: {cert_file}, {key_file}")
        return True
    
    print("生成自签名SSL证书...")
    
    try:
        # 使用openssl生成证书
        result = subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',  # 使用2048位更安全
            '-keyout', key_file, '-out', cert_file,
            '-days', '365', '-nodes',
            '-subj', '/C=CN/ST=Beijing/L=Beijing/O=JM Comic/CN=localhost'
        ], check=True, capture_output=True, text=True)
        
        print(f"SSL证书已生成: {cert_file}, {key_file}")
        
        # 设置适当的权限（非Windows系统）
        if os.name != 'nt':
            os.chmod(key_file, 0o600)  # 只有所有者可读写
            os.chmod(cert_file, 0o644)  # 所有者可读写，其他人只读
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"生成SSL证书失败: {e}")
        if e.stderr:
            print(f"错误详情: {e.stderr}")
        return False
    except Exception as e:
        print(f"生成SSL证书失败: {e}")
        return False

if __name__ == '__main__':
    if generate_ssl_certificates():
        print("✓ 证书生成成功")
        sys.exit(0)
    else:
        print("✗ 证书生成失败")
        sys.exit(1)
