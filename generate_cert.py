#!/usr/bin/env python3
"""
生成自签名SSL证书的Python脚本
"""
import os
import subprocess
import sys

def generate_cert_openssl():
    """使用openssl生成证书"""
    try:
        # 尝试不同的openssl命令格式
        cmd = [
            'openssl', 'req', '-x509',
            '-newkey', 'rsa:4096',
            '-nodes',
            '-out', 'cert.pem',
            '-keyout', 'key.pem',
            '-days', '365',
            '-subj', '/C=CN/ST=Beijing/L=Beijing/O=LocalDev/CN=localhost'
        ]
        
        print("正在生成SSL证书...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ SSL证书生成成功！")
            print(f"  证书文件: cert.pem")
            print(f"  私钥文件: key.pem")
            return True
        else:
            print(f"✗ OpenSSL错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 执行OpenSSL失败: {e}")
        return False

def generate_cert_python():
    """使用Python cryptography库生成证书（备用方案）"""
    try:
        # 尝试导入cryptography库
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        print("使用Python cryptography库生成证书...")
        
        # 生成私钥
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        
        # 生成证书
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LocalDev"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        ).sign(key, hashes.SHA256())
        
        # 保存私钥
        with open("key.pem", "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        
        # 保存证书
        with open("cert.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("✓ 使用Python成功生成SSL证书！")
        return True
        
    except ImportError:
        print("✗ 未安装cryptography库")
        return False
    except Exception as e:
        print(f"✗ Python生成证书失败: {e}")
        return False

def check_existing_cert():
    """检查是否已存在证书文件"""
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        print("✓ 发现已存在的证书文件")
        cert_size = os.path.getsize("cert.pem")
        key_size = os.path.getsize("key.pem")
        print(f"  证书大小: {cert_size} 字节")
        print(f"  私钥大小: {key_size} 字节")
        return True
    return False

def main():
    print("=" * 50)
    print("SSL证书生成工具")
    print("=" * 50)
    
    # 检查是否已存在证书
    if check_existing_cert():
        overwrite = input("证书已存在，是否重新生成？(y/n): ").strip().lower()
        if overwrite not in ['y', 'yes', '是']:
            print("使用现有证书")
            return True
    
    # 首先尝试使用openssl
    if generate_cert_openssl():
        return True
    
    print("\nOpenSSL生成失败，尝试使用Python cryptography库...")
    
    # 尝试安装cryptography库
    try:
        import pip
        install = input("是否安装cryptography库？(y/n): ").strip().lower()
        if install in ['y', 'yes', '是']:
            print("正在安装cryptography库...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    except:
        pass
    
    # 尝试使用Python生成
    if generate_cert_python():
        return True
    
    print("\n✗ 所有方法都失败了！")
    print("请手动生成证书：")
    print("1. 安装OpenSSL并正确配置")
    print("2. 或运行: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
    print("3. 或使用在线工具生成自签名证书")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)