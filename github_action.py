#!/usr/bin/env python3
"""
GitHub Action 专用脚本 - JM漫画下载和PDF转换
兼容最新版 JMComic
"""
import os
import sys
import time
import uuid
import shutil
from pathlib import Path

def setup_environment():
    """设置环境"""
    # 确保必要的目录存在
    directories = ['uploads', 'temp', 'outputs', 'download']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ 环境设置完成")

def safe_remove(path):
    """安全删除文件或目录"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"🗑️ 删除文件: {Path(path).name}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"🗑️ 删除目录: {Path(path).name}")
    except Exception as e:
        print(f"⚠️ 删除 {path} 失败: {e}")

def download_jm_comic(jm_id, download_dir):
    """
    使用JMComic下载漫画 - 兼容最新版本
    """
    try:
        print(f"📥 开始下载JM漫画 {jm_id}...")
        
        import jmcomic
        from jmcomic import JmOption, JmDownloader
        
        # 创建漫画目录
        comic_dir = os.path.join(download_dir, f"jm_{jm_id}")
        os.makedirs(comic_dir, exist_ok=True)
        
        print(f"📁 下载目录: {comic_dir}")
        
        # 新版 JMComic 配置方式
        try:
            # 方式1: 使用字典配置
            option_dict = {
                'dir_rule': {'base_dir': comic_dir},
                'download': {
                    'image': {'suffix': '.jpg'},
                    'threading': {'image': 3}
                },
                'client': {
                    'retry_times': 3,
                    'cache': True
                }
            }
            option = JmOption.construct(option_dict)
            
        except Exception as e:
            print(f"配置方式1失败: {e}")
            # 方式2: 使用默认配置并修改
            option = JmOption.default()
            option.dir_rule.base_dir = comic_dir
            option.download.image.suffix = '.jpg'
            option.download.threading.image = 3
        
        print(f"🎯 使用 JMComic 版本: {jmcomic.__version__}")
        
        # 创建下载器并下载
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
            # 显示目录内容帮助调试
            print("📂 目录内容:")
            try:
                for item in os.listdir(comic_dir):
                    item_path = os.path.join(comic_dir, item)
                    if os.path.isdir(item_path):
                        print(f"   📁 {item}/")
                        try:
                            for sub_item in os.listdir(item_path)[:5]:  # 只显示前5个文件
                                print(f"     📄 {sub_item}")
                        except:
                            print(f"     (无法读取子目录)")
                    else:
                        print(f"   📄 {item}")
            except Exception as e:
                print(f"   无法读取目录: {e}")
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
        
        # 清理原始图片目录以节省空间
        safe_remove(comic_dir)
        
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
        last_progress = 0
        
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
                            if os.path.exists(pdf):
                                pdf_size = os.path.getsize(pdf) / (1024 * 1024)
                                print(f"   - {Path(pdf).name} ({pdf_size:.1f} MB)")
                            else:
                                print(f"   - {Path(pdf).name} (文件不存在)")
                        
                        if zip_file and os.path.exists(zip_file):
                            zip_size = os.path.getsize(zip_file) / (1024 * 1024)
                            print(f"📦 完整包: {Path(zip_file).name} ({zip_size:.1f} MB)")
                    
                    return True
                    
                elif status['status'] == '错误':
                    print(f"❌ 处理失败: {status.get('error', '未知错误')}")
                    return False
                
                # 显示进度（只在进度更新时显示）
                progress = status.get('progress', 0)
                current_step = status.get('current_step', '')
                if progress != last_progress:
                    print(f"📊 进度: {progress}% - {current_step}")
                    last_progress = progress
            
            time.sleep(2)
        
        print("⏰ 处理超时")
        return False
        
    except Exception as e:
        print(f"❌ 处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_files():
    """清理临时文件"""
    try:
        # 直接使用文件操作而不是导入Flask组件
        temp_dirs = ['uploads', 'temp', 'outputs']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    safe_remove(item_path)
                print(f"🧹 清理 {temp_dir} 目录")
        
        # 清理download目录中的zip文件
        if os.path.exists('download'):
            for item in os.listdir('download'):
                if item.endswith('.zip'):
                    zip_path = os.path.join('download', item)
                    safe_remove(zip_path)
            
        print("✅ 文件清理完成")
            
    except Exception as e:
        print(f"⚠️ 清理文件时出错: {e}")

def check_download_results():
    """检查下载结果"""
    download_dir = 'download'
    if not os.path.exists(download_dir):
        print("❌ download 目录不存在")
        return False
    
    files = os.listdir(download_dir)
    if not files:
        print("❌ download 目录为空")
        return False
    
    pdf_files = [f for f in files if f.endswith('.pdf')]
    zip_files = [f for f in files if f.endswith('.zip')]
    
    print(f"📊 结果统计:")
    print(f"   PDF文件: {len(pdf_files)} 个")
    print(f"   ZIP文件: {len(zip_files)} 个")
    
    for file in files:
        file_path = os.path.join(download_dir, file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"   📄 {file} ({file_size:.1f} MB)")
        else:
            print(f"   📄 {file} (文件不存在)")
    
    return len(pdf_files) > 0 or len(zip_files) > 0

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
    
    try:
        # 下载漫画
        zip_path = download_jm_comic(jm_id, 'download')
        if not zip_path:
            print("❌ 漫画下载失败")
            sys.exit(1)
        
        # 转换为PDF
        success = process_comic_to_pdf(jm_id, zip_path, 'download')
        
        if success:
            print("\n🎉 任务完成!")
            
            # 检查最终结果
            print("\n📁 最终文件列表:")
            if check_download_results():
                print("✅ 文件生成成功，可在Artifacts中下载")
            else:
                print("❌ 未找到输出文件")
            
            # 清理临时文件
            print("\n🧹 清理临时文件...")
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