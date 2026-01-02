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
import json
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

def process_images_to_pdf_directly(image_files, output_dir, base_name="comic"):
    """
    直接处理图片文件为PDF，不依赖Flask的Web界面
    """
    try:
        print("🔄 直接转换图片为PDF...")
        
        from utils.image_processor import ImageProcessor
        from utils.pdf_generator import PDFGenerator
        
        # 处理图片
        image_processor = ImageProcessor()
        pdf_generator = PDFGenerator()
        
        # 设置状态回调
        def status_callback(message, progress=None):
            if progress:
                print(f"📊 {message} - {progress}%")
            else:
                print(f"📊 {message}")
        
        image_processor.set_status_callback(status_callback)
        pdf_generator.set_status_callback(status_callback)
        
        # 创建临时目录处理图片
        temp_dir = os.path.join(output_dir, "temp_process")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 处理图片
        status_callback("开始处理图片")
        processed_images = []
        
        for i, img_path in enumerate(image_files):
            progress = (i + 1) / len(image_files) * 50  # 图片处理占50%进度
            status_callback(f"处理图片 {i+1}/{len(image_files)}", progress)
            
            # 转换图片格式
            converted_path = image_processor.convert_to_supported_format(img_path, temp_dir)
            if converted_path:
                # 优化图片尺寸
                optimized_path = image_processor.optimize_image_for_pdf(converted_path)
                processed_images.append(optimized_path)
            else:
                # 如果转换失败，使用原图
                processed_images.append(img_path)
        
        # 生成PDF
        status_callback("开始生成PDF", 60)
        pdf_filename = f"{base_name}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        # 使用img2pdf直接生成PDF
        import img2pdf
        
        # 验证所有图片文件都存在
        valid_images = [img for img in processed_images if os.path.exists(img)]
        
        if not valid_images:
            status_callback("没有有效的图片文件", 100)
            return None
        
        # 生成PDF
        try:
            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(img2pdf.convert(valid_images))
            
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                status_callback(f"PDF生成成功: {pdf_filename}", 100)
                
                # 清理临时文件
                safe_remove(temp_dir)
                
                return pdf_path
            else:
                status_callback("PDF文件生成失败", 100)
                return None
                
        except Exception as e:
            status_callback(f"PDF生成失败: {e}", 100)
            return None
            
    except Exception as e:
        print(f"❌ 直接PDF转换失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_images_from_zip(zip_path, extract_dir):
    """从ZIP文件中提取图片"""
    try:
        import zipfile
        
        print(f"📂 从ZIP文件提取图片: {Path(zip_path).name}")
        
        image_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取所有文件列表
            file_list = zip_ref.namelist()
            
            # 过滤图片文件
            image_files_in_zip = [f for f in file_list if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'))]
            
            if not image_files_in_zip:
                print("❌ ZIP文件中没有找到图片文件")
                return None
            
            print(f"✅ 在ZIP中找到 {len(image_files_in_zip)} 张图片")
            
            # 提取文件
            for i, file_info in enumerate(image_files_in_zip):
                # 解压文件
                zip_ref.extract(file_info, extract_dir)
                extracted_path = os.path.join(extract_dir, file_info)
                image_files.append(extracted_path)
                
                if (i + 1) % 10 == 0:  # 每10个文件显示一次进度
                    print(f"📥 已提取 {i+1}/{len(image_files_in_zip)} 张图片")
        
        # 按文件名自然排序
        import re
        image_files.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() 
                                      for text in re.split(r'(\d+)', x)])
        
        return image_files
        
    except Exception as e:
        print(f"❌ 提取ZIP文件失败: {e}")
        return None

def create_download_package(pdf_files, output_dir, jm_id):
    """创建下载包"""
    try:
        if not pdf_files:
            print("❌ 没有PDF文件可打包")
            return None
        
        # 如果只有一个PDF文件，直接返回
        if len(pdf_files) == 1:
            print(f"📄 单个PDF文件: {Path(pdf_files[0]).name}")
            return pdf_files[0]
        
        # 多个PDF文件，打包成ZIP
        import zipfile
        zip_filename = f"jm_{jm_id}_pdfs.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        print(f"📦 打包 {len(pdf_files)} 个PDF文件...")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pdf_file in pdf_files:
                if os.path.exists(pdf_file):
                    arcname = Path(pdf_file).name
                    zipf.write(pdf_file, arcname)
                    print(f"   + {arcname}")
        
        if os.path.exists(zip_path) and os.path.getsize(zip_path) > 0:
            print(f"✅ 打包完成: {zip_filename}")
            return zip_path
        else:
            print("❌ 打包失败")
            return None
            
    except Exception as e:
        print(f"❌ 创建下载包失败: {e}")
        return None

def process_comic_directly(jm_id, zip_path, download_dir):
    """
    直接处理漫画，不依赖Flask Web界面
    """
    try:
        print("🔄 开始直接处理漫画文件...")
        
        # 创建临时提取目录
        extract_dir = os.path.join(download_dir, f"extract_{jm_id}")
        os.makedirs(extract_dir, exist_ok=True)
        
        # 从ZIP提取图片
        image_files = extract_images_from_zip(zip_path, extract_dir)
        if not image_files:
            print("❌ 图片提取失败")
            safe_remove(extract_dir)
            return False
        
        print(f"✅ 成功提取 {len(image_files)} 张图片")
        
        # 直接转换为PDF
        pdf_path = process_images_to_pdf_directly(image_files, download_dir, f"jm_{jm_id}")
        
        # 清理临时文件
        safe_remove(extract_dir)
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"🎉 PDF生成成功: {Path(pdf_path).name}")
            
            # 创建结果清单
            result_files = [pdf_path]
            final_package = create_download_package(result_files, download_dir, jm_id)
            
            if final_package:
                print(f"📦 最终文件: {Path(final_package).name}")
                return True
            else:
                print("✅ 单个PDF文件已生成")
                return True
        else:
            print("❌ PDF生成失败")
            return False
            
    except Exception as e:
        print(f"❌ 直接处理失败: {e}")
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
        
        # 清理download目录中的zip文件（保留PDF）
        if os.path.exists('download'):
            for item in os.listdir('download'):
                if item.endswith('.zip') and 'jm_' in item:
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
    
    total_size = 0
    for file in files:
        file_path = os.path.join(download_dir, file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            total_size += file_size
            print(f"   📄 {file} ({file_size:.1f} MB)")
        else:
            print(f"   📄 {file} (文件不存在)")
    
    print(f"📦 总大小: {total_size:.1f} MB")
    
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
        
        # 直接处理为PDF（不依赖Web界面）
        success = process_comic_directly(jm_id, zip_path, 'download')
        
        if success:
            print("\n🎉 任务完成!")
            
            # 检查最终结果
            print("\n📁 最终文件列表:")
            if check_download_results():
                print("✅ 文件生成成功，可在Artifacts中下载")
                print("💡 在GitHub Actions页面点击 'Artifacts' 下载生成的文件")
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