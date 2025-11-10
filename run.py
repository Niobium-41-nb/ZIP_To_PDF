#!/usr/bin/env python3
"""
Flask压缩包转PDF工具 - 启动脚本
支持JM漫画下载并转换为PDF
"""
import os
import sys
import webbrowser
import threading
import time
import argparse
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
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
            print(f" - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False

    return True

def open_browser():
    """在浏览器中打开应用"""
    time.sleep(2)  # 等待应用启动
    webbrowser.open('http://localhost:5000')

def setup_download_directory():
    """设置下载目录"""
    download_dir = os.path.join(os.getcwd(), 'download')
    os.makedirs(download_dir, exist_ok=True)
    return download_dir

def cleanup_temp_files(task_id=None):
    """清理临时文件"""
    try:
        from app import app
        from utils.file_utils import FileUtils
        
        if task_id:
            # 清理指定任务的文件
            FileUtils.cleanup_task_files(
                task_id,
                app.config['UPLOAD_FOLDER'],
                app.config['TEMP_FOLDER'],
                app.config['OUTPUT_FOLDER']
            )
            print(f"已清理任务 {task_id} 的临时文件")
        else:
            # 清理所有临时文件
            FileUtils.cleanup_old_files(app.config['UPLOAD_FOLDER'], hours_old=0)
            FileUtils.cleanup_old_files(app.config['TEMP_FOLDER'], hours_old=0)
            print("已清理所有临时文件")
            
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

def download_jm_comic(jm_id, download_dir):
    """
    使用JMComic下载漫画到download目录
    """
    try:
        print(f"开始下载JM漫画 {jm_id}...")
        
        # 检查是否安装了jmcomic
        try:
            import jmcomic
            from jmcomic import JmOption, JmDownloader
        except ImportError:
            print("未安装JMComic库，正在尝试安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "jmcomic", "-i", "https://pypi.org/project"])
            import jmcomic
            from jmcomic import JmOption, JmDownloader
        
        # 在download目录下创建漫画子目录
        comic_dir = os.path.join(download_dir, f"jm_{jm_id}")
        os.makedirs(comic_dir, exist_ok=True)
        
        print(f"下载目录: {comic_dir}")
        
        # 正确的方式创建配置
        try:
            # 方式1: 使用字典配置
            option_dict = {
                'dir_rule': {'base_dir': comic_dir},
                'download': {
                    'image': {'suffix': '.jpg'},
                    'threading': {'image': 3}
                }
            }
            
            # 创建选项对象
            option = JmOption.construct(option_dict)
            
        except Exception as e:
            print(f"配置创建失败: {e}")
            # 方式2: 使用默认配置并修改目录
            option = JmOption.default()
            option.dir_rule.base_dir = comic_dir
        
        # 创建下载器并下载
        downloader = JmDownloader(option)
        downloader.download_album(jm_id)
        
        # 查找下载的图片文件
        image_files = []
        for root, dirs, files in os.walk(comic_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            print("未找到下载的图片文件")
            # 检查目录结构
            print("目录内容:")
            for root, dirs, files in os.walk(comic_dir):
                level = root.replace(comic_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    print(f"{subindent}{file}")
            return None
        
        print(f"找到 {len(image_files)} 张图片")
        
        # 按文件名自然排序
        image_files.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() 
                                      for text in re.split(r'(\d+)', x)])
        
        # 创建ZIP文件用于后续处理
        import zipfile
        zip_path = os.path.join(download_dir, f"jm_{jm_id}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i, img_path in enumerate(image_files):
                # 确保文件名格式统一
                arcname = f"{i:04d}{Path(img_path).suffix}"
                zipf.write(img_path, arcname)
        
        print(f"漫画已打包为: {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"下载JM漫画失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_jm_comic(jm_id):
    """
    处理JM漫画下载和转换
    """
    try:
        from app import app, process_compressed_file, processing_status, processing_results
        import uuid
        
        # 设置下载目录
        download_dir = setup_download_directory()
        
        # 下载漫画
        zip_path = download_jm_comic(jm_id, download_dir)
        if not zip_path:
            print("漫画下载失败")
            return False
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 设置输出目录为download目录
        output_dir = download_dir
        
        print("开始处理漫画文件...")
        
        # 在后台线程中处理
        thread = threading.Thread(
            target=process_compressed_file,
            args=(task_id, zip_path, output_dir)
        )
        thread.daemon = True
        thread.start()
        
        # 轮询处理状态
        print("处理中", end="", flush=True)
        max_wait_time = 600  # 最大等待时间10分钟
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if task_id in processing_status:
                status = processing_status[task_id]
                
                if status['status'] == '处理完成':
                    print("\n✓ 处理完成!")
                    
                    # 显示结果
                    if task_id in processing_results:
                        result = processing_results[task_id]
                        pdf_files = result.get('pdf_files', [])
                        zip_file = result.get('zip_file')
                        
                        print(f"\n生成 {len(pdf_files)} 个PDF文件:")
                        for pdf in pdf_files:
                            pdf_size = os.path.getsize(pdf) / (1024 * 1024)  # MB
                            print(f"  📄 {os.path.basename(pdf)} ({pdf_size:.1f} MB)")
                        
                        if zip_file and os.path.exists(zip_file):
                            zip_size = os.path.getsize(zip_file) / (1024 * 1024)  # MB
                            print(f"\n📦 完整包: {os.path.basename(zip_file)} ({zip_size:.1f} MB)")
                            
                        # 显示下载目录
                        print(f"\n📁 文件保存在: {download_dir}")
                        
                        # 询问是否打开目录
                        open_dir = input("\n是否打开下载目录? (y/n): ").lower().strip()
                        if open_dir in ['y', 'yes', '是']:
                            if sys.platform == "win32":
                                os.startfile(download_dir)
                            elif sys.platform == "darwin":
                                subprocess.Popen(["open", download_dir])
                            else:
                                subprocess.Popen(["xdg-open", download_dir])
                    
                    # 清理临时文件
                    cleanup_choice = input("\n是否清理临时文件? (y/n): ").lower().strip()
                    if cleanup_choice in ['y', 'yes', '是']:
                        cleanup_temp_files(task_id)
                    
                    return True
                    
                elif status['status'] == '错误':
                    print(f"\n✗ 处理失败: {status.get('error', '未知错误')}")
                    # 清理临时文件
                    cleanup_temp_files(task_id)
                    return False
                
                # 显示进度
                progress = status.get('progress', 0)
                current_step = status.get('current_step', '')
                if progress > 0:
                    print(f"\r处理中: {progress}% - {current_step}", end="", flush=True)
                    
            time.sleep(2)
        
        print(f"\n⏰ 处理超时（超过{max_wait_time//60}分钟）")
        cleanup_temp_files(task_id)
        return False
            
    except Exception as e:
        print(f"\n❌ 处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
        cleanup_temp_files()
        return False

def start_web_app():
    """启动Web应用"""
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
        cleanup_temp_files()
    except Exception as e:
        print(f"启动失败: {e}")
        return False

def cleanup_all_downloads():
    """清理所有下载文件（可选功能）"""
    try:
        download_dir = setup_download_directory()
        if os.path.exists(download_dir):
            for filename in os.listdir(download_dir):
                file_path = os.path.join(download_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"删除 {filename} 失败: {e}")
        
        print("已清理所有下载文件")
        return True
    except Exception as e:
        print(f"清理下载文件失败: {e}")
        return False

def cleanup_all_temp_files():
    """
    专门清理temp文件夹中的所有内容
    包括所有临时任务文件夹、PNG图片和压缩包
    """
    try:
        from config import config
        
        config_obj = config['default']
        temp_dir = config_obj.TEMP_FOLDER
        
        print("开始清理temp文件夹...")
        
        if not os.path.exists(temp_dir):
            print(f"temp文件夹不存在: {temp_dir}")
            return True
        
        # 统计信息
        total_files = 0
        total_size = 0
        
        # 递归遍历temp文件夹
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # 删除所有文件，不限制类型
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    print(f"已删除: {os.path.relpath(file_path, temp_dir)} ({file_size / 1024 / 1024:.1f} MB)")
                    total_files += 1
                    total_size += file_size
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
            
            # 删除空文件夹（除了temp根目录）
            if root != temp_dir:
                try:
                    # 检查文件夹是否为空
                    if not os.listdir(root):
                        os.rmdir(root)
                        print(f"已删除空文件夹: {os.path.relpath(root, temp_dir)}")
                except Exception as e:
                    print(f"删除文件夹失败 {root}: {e}")
        
        # 显示清理结果
        if total_files > 0:
            print(f"\n清理完成！")
            print(f"总计: 删除 {total_files} 个文件，释放 {total_size / 1024 / 1024:.1f} MB 空间")
        else:
            print("temp文件夹为空，无需清理")
        
        return True
        
    except Exception as e:
        print(f"清理temp文件夹失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def is_github_actions():
    """检查是否在 GitHub Actions 环境中运行"""
    return os.getenv('GITHUB_ACTIONS') == 'true'

def download_random_jm_comic():
    """下载随机JM漫画"""
    try:
        # 生成随机ID
        jm_id = str(random.randint(100000, 999999))
        print(f"生成的随机JM ID: {jm_id}")
        
        # 使用现有的下载逻辑
        return process_jm_comic(jm_id)
    except Exception as e:
        print(f"随机下载失败: {e}")
        return False

def batch_download_random_comics(count=5):
    """批量下载随机漫画"""
    success_count = 0
    for i in range(count):
        print(f"\n正在下载第 {i+1}/{count} 个随机漫画...")
        if download_random_jm_comic():
            success_count += 1
        # 添加延迟避免请求过快
        time.sleep(2)
    
    print(f"\n批量下载完成！成功: {success_count}/{count}")
    return success_count

def main():
    """主函数"""
    print("=" * 50)
    print("Flask压缩包转PDF工具 - JM漫画下载版")
    print("=" * 50)
    
    # 设置下载目录
    download_dir = setup_download_directory()
    print(f"下载目录: {download_dir}")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='JM漫画下载和PDF转换工具')
    parser.add_argument('jm_id', nargs='?', help='JM漫画ID')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--cleanup', action='store_true', help='清理所有下载文件')
    parser.add_argument('--cleanup-temp', action='store_true', help='清理临时文件')
    parser.add_argument('--cleanup-all-temp', action='store_true', help='清理temp文件夹中的所有内容')
    
    args = parser.parse_args()
    
    # # 检查依赖
    # print("检查依赖包...")
    # if not check_dependencies():
    #     sys.exit(1)
    
    # 创建必要目录
    print("创建项目目录...")
    FileUtils.create_directories()
    
    if is_github_actions():
        # 在 GitHub Actions 中使用简化模式
        if args.jm_id:
            from github_action import main as github_main
            github_main(args.jm_id)
        return
    elif args.cleanup:
        # 清理下载文件
        cleanup_all_downloads()
        return
    elif args.cleanup_temp:
        # 清理临时文件
        cleanup_temp_files()
        return
    elif args.cleanup_all_temp:
        # 清理temp文件夹中的所有内容
        cleanup_all_temp_files()
        return
    elif args.web:
        # 启动Web应用
        start_web_app()
    elif args.jm_id:
        # 直接处理指定的JM漫画
        if not args.jm_id.isdigit():
            print("错误: JM ID必须是数字")
            sys.exit(1)
            
        success = process_jm_comic(args.jm_id)
        sys.exit(0 if success else 1)
    else:
        # 交互模式
        print("\n请选择模式:")
        print("1. 启动Web界面")
        print("2. 下载JM漫画并转换为PDF")
        print("3. 随机下载JM漫画")
        print("4. 批量随机下载JM漫画")
        print("5. 清理下载文件")
        print("6. 清理临时文件")
        print("7. 清理temp文件夹中的所有内容")
        
        choice = input("\n请输入选择 (1-7): ").strip()
        
        if choice == '1':
            start_web_app()
        elif choice == '2':
            jm_id = input("请输入JM漫画ID: ").strip()
            if jm_id and jm_id.isdigit():
                process_jm_comic(jm_id)
            else:
                print("无效的JM ID")
        elif choice == '3':
            print("开始随机下载JM漫画...")
            download_random_jm_comic()
        elif choice == '4':
            count = input("请输入要下载的数量 (1-10): ").strip()
            try:
                count = int(count)
                if count < 1:
                    count = 1
                elif count > 10:
                    count = 10
                batch_download_random_comics(count)
            except ValueError:
                print("无效的数量，使用默认值 5")
                batch_download_random_comics(5)
        elif choice == '5':
            cleanup_all_downloads()
        elif choice == '6':
            cleanup_temp_files()
        elif choice == '7':
            cleanup_all_temp_files()
        else:
            print("无效的选择")

if __name__ == '__main__':
    main()