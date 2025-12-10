#!/usr/bin/env python3
"""
Docker配置测试脚本
用于验证Dockerfile和docker-compose.yml配置是否正确
"""

import os
import sys
import subprocess
import yaml

def check_file_exists(filepath):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✓ {filepath} 存在")
        return True
    else:
        print(f"✗ {filepath} 不存在")
        return False

def check_dockerfile():
    """检查Dockerfile"""
    print("\n1. 检查Dockerfile...")
    if not check_file_exists("Dockerfile"):
        return False
    
    with open("Dockerfile", "r", encoding="utf-8") as f:
        content = f.read()
        
    checks = [
        ("FROM python:", "Python基础镜像"),
        ("WORKDIR /app", "工作目录设置"),
        ("COPY requirements.txt", "复制依赖文件"),
        ("RUN pip install", "安装Python依赖"),
        ("EXPOSE", "暴露端口"),
        ("CMD", "启动命令"),
    ]
    
    all_ok = True
    for check_str, description in checks:
        if check_str in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ 缺少: {description}")
            all_ok = False
            
    return all_ok

def check_docker_compose():
    """检查docker-compose.yml"""
    print("\n2. 检查docker-compose.yml...")
    if not check_file_exists("docker-compose.yml"):
        return False
    
    try:
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        if 'services' not in config:
            print("  ✗ 缺少services配置")
            return False
            
        service_name = 'jm-tag-to-pdf'
        if service_name not in config['services']:
            print(f"  ✗ 缺少服务: {service_name}")
            return False
            
        service = config['services'][service_name]
        
        checks = [
            ("build", "构建配置"),
            ("ports", "端口映射"),
            ("volumes", "数据卷"),
            ("environment", "环境变量"),
        ]
        
        all_ok = True
        for check_key, description in checks:
            if check_key in service:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ 缺少: {description}")
                all_ok = False
                
        # 检查端口配置
        if 'ports' in service:
            ports = service['ports']
            if "8443:8443" in ports or any("8443" in str(p) for p in ports):
                print("  ✓ HTTPS端口配置 (8443)")
            else:
                print("  ✗ 缺少HTTPS端口配置")
                all_ok = False
                
        return all_ok
        
    except yaml.YAMLError as e:
        print(f"  ✗ YAML解析错误: {e}")
        return False
    except Exception as e:
        print(f"  ✗ 检查错误: {e}")
        return False

def check_requirements():
    """检查requirements.txt"""
    print("\n3. 检查requirements.txt...")
    if not check_file_exists("requirements.txt"):
        return False
    
    with open("requirements.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    required_packages = [
        "Flask",
        "Pillow",
        "img2pdf",
        "python-magic",
        "rarfile",
        "py7zr",
        "jmcomic",
        "Werkzeug",
    ]
    
    found_packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            for pkg in required_packages:
                if pkg.lower() in line.lower():
                    found_packages.append(pkg)
                    
    all_ok = True
    for pkg in required_packages:
        if pkg in found_packages:
            print(f"  ✓ {pkg}")
        else:
            print(f"  ✗ 缺少: {pkg}")
            all_ok = False
            
    return all_ok

def check_directories():
    """检查必要的目录"""
    print("\n4. 检查项目目录结构...")
    
    required_dirs = [
        "uploads",
        "download",
        "outputs",
        "logs",
        "temp",
        "static/css",
        "static/js",
        "templates",
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ 缺少目录: {dir_path}/")
            all_ok = False
            
    return all_ok

def check_docker_installation():
    """检查Docker安装"""
    print("\n5. 检查Docker安装...")
    
    try:
        # 检查Docker版本
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"  ✓ Docker已安装: {result.stdout.strip()}")
            
            # 检查Docker Compose
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"  ✓ Docker Compose已安装: {result.stdout.strip()}")
            else:
                # 检查Docker Compose插件
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    print(f"  ✓ Docker Compose插件已安装: {result.stdout.strip()}")
                else:
                    print("  ⚠ Docker Compose未安装，但可以使用docker compose命令")
                    
            return True
        else:
            print("  ✗ Docker未安装或未运行")
            return False
            
    except FileNotFoundError:
        print("  ✗ Docker命令未找到")
        return False
    except Exception as e:
        print(f"  ✗ 检查Docker时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("JM-tag.zip_to_PDF Docker配置测试")
    print("=" * 60)
    
    tests = [
        ("Dockerfile检查", check_dockerfile),
        ("Docker Compose检查", check_docker_compose),
        ("依赖文件检查", check_requirements),
        ("目录结构检查", check_directories),
        ("Docker安装检查", check_docker_installation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  测试出错: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n✅ 所有测试通过！Docker配置正确。")
        print("\n下一步:")
        print("1. 构建镜像: docker-compose build")
        print("2. 启动服务: docker-compose up -d")
        print("3. 访问应用: https://localhost:8443")
        return 0
    else:
        print("\n❌ 有测试失败，请检查上述问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())