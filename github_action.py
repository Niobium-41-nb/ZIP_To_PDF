#!/usr/bin/env python3
"""
GitHub Action 专用脚本 - JM漫画下载和PDF转换
"""
import os
import sys
import time
import uuid
from pathlib import Path

def setup_environment():
    """设置环境"""
    # 确保必要的目录存在
    directories = ['uploads', 'temp', 'outputs', 'download']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ 环境设置完成")

def download_jm_comic(jm_id, download_dir):
    """
    使用JMComic下载漫画
    """
    try:
        print(f"📥 开始下载JM漫画 {jm_id}...")
        
        import jmcomic
        from jmcomic import JmOption, JmDownloader
        
        # 创建漫画目录
        comic_dir = os.path.join(download_dir, f"jm_{jm_id}")
        os.makedirs(comic_dir, exist_ok=True)
        
        print(f"📁 下载目录: {comic_dir}")
        
        # 配置下载选项
        option = JmOption.default()
        option.dir_rule.base_dir = comic_dir
        option.download.image.suffix = '.jpg'
        option.download.threading.image = 3
        
        # 下载漫画
        downloader = JmDownloader(option)
        downloader.download_album(jm_id)
        
        # 查找图片文件
        image_files = []
        for root, dirs, files in os.walk(comic_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            print("❌ 未找到下载的图片文件")
            return None
        
        print(f"✅ 找到 {len(image_files)} 张图片")
        
        # 按文件名自然排序
        import re
        image_files.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() 
                                      for text in re.split(r'(\d+)', x)])
        
        # 创建ZIP文件
        import zipfile
        zip_path = os.path.join(download_dir, f"jm_{jm_id}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i, img_path in enumerate(image_files):
                arcname = f"{i:04d}{Path(img_path).suffix}"
                zipf.write(img_path, arcname)
        
        print(f"📦 漫画已打包为: {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"❌ 下载JM漫画失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_comic_to_pdf(jm_id, zip_path, download_dir):
    """
    处理漫画转换为PDF
    """
    try:
        # 导入Flask应用组件
        from app import process_compressed_file, processing_status, processing_results
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        print("🔄 开始处理漫画文件...")
        
        # 在后台处理
        import threading
        thread = threading.Thread(
            target=process_compressed_file,
            args=(task_id, zip_path, download_dir)
        )
        thread.daemon = True
        thread.start()
        
        # 轮询处理状态
        max_wait_time = 600  # 10分钟
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if task_id in processing_status:
                status = processing_status[task_id]
                
                if status['status'] == '处理完成':
                    print("✅ 处理完成!")
                    
                    if task_id in processing_results:
                        result = processing_results[task_id]
                        pdf_files = result.get('pdf_files', [])
                        zip_file = result.get('zip_file')
                        
                        print(f"📄 生成 {len(pdf_files)} 个PDF文件:")
                        for pdf in pdf_files:
                            pdf_size = os.path.getsize(pdf) / (1024 * 1024)
                            print(f"   - {Path(pdf).name} ({pdf_size:.1f} MB)")
                        
                        if zip_file and os.path.exists(zip_file):
                            zip_size = os.path.getsize(zip_file) / (1024 * 1024)
                            print(f"📦 完整包: {Path(zip_file).name} ({zip_size:.1f} MB)")
                    
                    return True
                    
                elif status['status'] == '错误':
                    print(f"❌ 处理失败: {status.get('error', '未知错误')}")
                    return False
                
                # 显示进度
                progress = status.get('progress', 0)
                current_step = status.get('current_step', '')
                if progress > 0:
                    print(f"📊 进度: {progress}% - {current_step}")
            
            time.sleep(2)
        
        print("⏰ 处理超时")
        return False
        
    except Exception as e:
        print(f"❌ 处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_files(task_id=None):
    """清理文件"""
    try:
        from app import app
        from utils.file_utils import FileUtils
        
        if task_id:
            FileUtils.cleanup_task_files(
                task_id,
                app.config['UPLOAD_FOLDER'],
                app.config['TEMP_FOLDER'],
                app.config['OUTPUT_FOLDER']
            )
            print(f"🧹 已清理任务 {task_id} 的临时文件")
        else:
            FileUtils.cleanup_old_files(app.config['UPLOAD_FOLDER'], hours_old=0)
            FileUtils.cleanup_old_files(app.config['TEMP_FOLDER'], hours_old=0)
            print("🧹 已清理所有临时文件")
            
    except Exception as e:
        print(f"⚠️ 清理文件时出错: {e}")

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python github_action.py <JM_ID>")
        sys.exit(1)
    
    jm_id = sys.argv[1]
    
    print("=" * 50)
    print("🎯 GitHub Action - JM漫画下载转换")
    print("=" * 50)
    
    # 设置环境
    setup_environment()
    
    # 设置下载目录
    download_dir = 'download'
    
    try:
        # 下载漫画
        zip_path = download_jm_comic(jm_id, download_dir)
        if not zip_path:
            print("❌ 漫画下载失败")
            sys.exit(1)
        
        # 转换为PDF
        success = process_comic_to_pdf(jm_id, zip_path, download_dir)
        
        if success:
            print("\n🎉 任务完成!")
            
            # 显示最终文件列表
            print("\n📁 生成的文件:")
            for file in os.listdir(download_dir):
                if file.endswith(('.pdf', '.zip')):
                    file_path = os.path.join(download_dir, file)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"   - {file} ({file_size:.1f} MB)")
            
            # 清理临时文件
            cleanup_files()
            
        else:
            print("❌ 任务失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()