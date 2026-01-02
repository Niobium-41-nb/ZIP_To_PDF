#!/usr/bin/env python3
"""
GitGuardian安全修复脚本
解决RSA私钥泄露问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    print("=" * 70)
    print("GitGuardian安全修复工具")
    print("解决RSA私钥泄露问题")
    print("=" * 70)

def check_prerequisites():
    """检查前置条件"""
    print("\n1. 检查前置条件...")
    
    # 检查Git
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        print("   ✓ Git已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ✗ Git未安装或不在PATH中")
        return False
    
    # 检查是否在Git仓库中
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                              capture_output=True, text=True, check=True)
        git_root = result.stdout.strip()
        print(f"   ✓ Git仓库: {git_root}")
        return True
    except subprocess.CalledProcessError:
        print("   ✗ 当前目录不是Git仓库")
        return False

def backup_sensitive_files():
    """备份敏感文件"""
    print("\n2. 备份敏感文件...")
    
    sensitive_files = ['key.pem', 'cert.pem']
    backup_dir = Path('.secrets_backup')
    
    if not backup_dir.exists():
        backup_dir.mkdir(exist_ok=True)
    
    backed_up = []
    for file in sensitive_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir / file)
            backed_up.append(file)
            print(f"   ✓ 备份: {file}")
    
    if backed_up:
        print(f"   备份位置: {backup_dir}/")
    else:
        print("   未找到敏感文件需要备份")
    
    return backup_dir

def remove_from_git():
    """从Git中移除敏感文件"""
    print("\n3. 从Git中移除敏感文件...")
    
    sensitive_files = ['key.pem', 'cert.pem']
    
    for file in sensitive_files:
        if not os.path.exists(file):
            print(f"   跳过: {file} 不存在")
            continue
        
        print(f"   处理: {file}")
        
        # 从Git索引中移除
        try:
            subprocess.run(['git', 'rm', '--cached', file], check=True, capture_output=True)
            print(f"     ✓ 从索引中移除")
        except subprocess.CalledProcessError:
            print(f"     ⚠ 无法从索引中移除（可能未跟踪）")
        
        # 添加到.gitignore（如果尚未添加）
        gitignore_path = '.gitignore'
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file not in content:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write(f'\n{file}')
                print(f"     ✓ 添加到.gitignore")
    
    print("   所有敏感文件已从Git中移除")

def generate_safe_cert_script():
    """生成安全的证书生成脚本"""
    print("\n4. 创建安全证书生成机制...")
    
    # 创建证书生成脚本
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_path = 'generate_cert_safe.py'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    if os.name != 'nt':
        os.chmod(script_path, 0o755)
    
    print(f"   ✓ 安全证书生成脚本: {script_path}")
    
    # 更新Dockerfile以使用新脚本
    update_dockerfile_for_safety()
    
    return script_path

def update_dockerfile_for_safety():
    """更新Dockerfile以安全生成证书"""
    print("\n5. 更新Docker配置...")
    
    dockerfile_path = 'Dockerfile'
    if not os.path.exists(dockerfile_path):
        print("   ⚠ Dockerfile不存在")
        return
    
    with open(dockerfile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保Dockerfile在运行时生成证书，而不是构建时
    if 'RUN if [ ! -f cert.pem ]' in content:
        print("   ✓ Dockerfile已配置为运行时生成证书")
    else:
        print("   ⚠ 检查Dockerfile证书生成逻辑")
    
    # 确保证书文件不被复制到镜像中
    if 'COPY cert.pem' in content or 'COPY key.pem' in content:
        print("   ⚠ 警告: Dockerfile可能复制了证书文件")
    else:
        print("   ✓ Dockerfile未复制证书文件")

def update_gitignore_comprehensive():
    """全面更新.gitignore"""
    print("\n6. 更新.gitignore文件...")
    
    gitignore_path = '.gitignore'
    security_patterns = [
        '\n# ====== 安全敏感文件（永远不要提交） ======',
        '# SSL证书和私钥',
        '*.pem',
        '*.key',
        '*.crt',
        '*.csr',
        'cert.pem',
        'key.pem',
        '# 环境变量和配置文件',
        '.env',
        '.env.*',
        'secrets.*',
        'config.local.*',
        '# 备份目录',
        '.secrets_backup/',
        '# 临时敏感文件',
        '*.tmp.key',
        '*.tmp.cert'
    ]
    
    if not os.path.exists(gitignore_path):
        print("   ⚠ .gitignore不存在，正在创建...")
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(security_patterns))
        print("   ✓ .gitignore已创建")
        return
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加缺失的安全模式
    added = False
    for pattern in security_patterns:
        if pattern.strip() and pattern not in content and not pattern.startswith('#'):
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write(f'\n{pattern}')
            added = True
    
    if added:
        print("   ✓ .gitignore已更新安全模式")
    else:
        print("   ✓ .gitignore已包含所有安全模式")

def print_remediation_steps():
    """打印修复步骤"""
    print("\n" + "=" * 70)
    print("安全修复完成！请执行以下步骤：")
    print("=" * 70)
    
    print("\n📋 立即操作：")
    print("1. 验证敏感文件已从Git索引中移除：")
    print("   git status")
    print("   应该显示key.pem和cert.pem为'deleted'或不在跟踪列表中")
    
    print("\n2. 提交更改：")
    print("   git add .gitignore")
    print("   git commit -m \"security: remove sensitive files from git and update .gitignore\"")
    
    print("\n3. 从Git历史中彻底移除敏感文件（如果需要）：")
    print("   如果敏感文件已经提交到历史中，需要重写历史：")
    print("   git filter-branch --force --index-filter \\")
    print("     \"git rm --cached --ignore-unmatch key.pem cert.pem\" \\")
    print("     --prune-empty --tag-name-filter cat -- --all")
    
    print("\n4. 强制推送到远程仓库：")
    print("   git push origin --force --all")
    print("   git push origin --force --tags")
    print("   ⚠ 警告：这会重写历史，确保团队知晓")
    
    print("\n5. 清理本地仓库：")
    print("   git for-each-ref --format='%(refname)' refs/original/ | \\")
    print("     xargs -n 1 git update-ref -d")
    print("   git reflog expire --expire=now --all")
    print("   git gc --prune=now --aggressive")
    
    print("\n🔒 长期安全措施：")
    print("1. 使用环境变量存储敏感信息：")
    print("   export SSL_KEY_PATH=./key.pem")
    print("   export SSL_CERT_PATH=./cert.pem")
    
    print("\n2. 使用密钥管理服务：")
    print("   - AWS Secrets Manager")
    print("   - Azure Key Vault")
    print("   - HashiCorp Vault")
    
    print("\n3. 设置预提交钩子防止再次提交敏感信息：")
    print("   创建 .git/hooks/pre-commit 检查敏感文件")
    
    print("\n4. 定期轮换证书：")
    print("   每90天生成新证书")
    print("   python generate_cert_safe.py")
    
    print("\n5. 监控GitGuardian警报：")
    print("   定期检查仪表板，确保没有新的泄露")
    
    print("\n🛡️ 验证修复：")
    print("1. 运行测试确保应用仍能正常工作：")
    print("   python test_docker.py")
    
    print("\n2. 验证Docker构建：")
    print("   docker build -t security-test .")
    
    print("\n3. 等待GitGuardian重新扫描：")
    print("   通常需要几分钟到几小时")
    
    print("\n" + "=" * 70)
    print("如需帮助，请参考：")
    print("- GitGuardian文档: https://docs.gitguardian.com")
    print("- GitHub安全指南: https://docs.github.com/en/code-security")
    print("=" * 70)

def main():
    """主函数"""
    print_header()
    
    # 检查前置条件
    if not check_prerequisites():
        print("\n✗ 前置条件检查失败")
        return 1
    
    # 备份敏感文件
    backup_dir = backup_sensitive_files()
    
    # 从Git中移除
    remove_from_git()
    
    # 生成安全证书脚本
    generate_safe_cert_script()
    
    # 更新Dockerfile
    update_dockerfile_for_safety()
    
    # 更新.gitignore
    update_gitignore_comprehensive()
    
    # 打印修复步骤
    print_remediation_steps()
    
    print("\n✅ 安全修复脚本执行完成！")
    print("请按照上述步骤操作以彻底解决安全问题。")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)