#!/usr/bin/env python3
"""
文件清理脚本
用于清理上传文件、临时文件和旧的输出文件
"""

import os
import time
from config import config
from utils.file_utils import FileUtils

def cleanup_all_files():
    """清理所有临时和旧文件"""
    print("开始清理所有文件...")
    
    config_obj = config['default']
    
    # 确保目录存在
    FileUtils.create_directories()
    
    # 清理上传文件夹（保留24小时内的文件）
    print("清理上传文件夹...")
    FileUtils.cleanup_old_files(config_obj.UPLOAD_FOLDER, hours_old=24)
    
    # 清理临时文件夹（保留12小时内的文件）
    print("清理临时文件夹...")
    FileUtils.cleanup_old_files(config_obj.TEMP_FOLDER, hours_old=12)
    
    # 清理输出文件夹（保留48小时内的文件）
    print("清理输出文件夹...")
    FileUtils.cleanup_old_files(config_obj.OUTPUT_FOLDER, hours_old=48)

    # 清理输出文件夹（保留48小时内的文件）
    print("清理下载文件夹...")
    FileUtils.cleanup_old_files(config_obj.DOWNLOAD_FOLDER, hours_old=0)
    
    print("文件清理完成！")

def cleanup_task_files(task_id):
    """清理指定任务的所有文件"""
    print(f"清理任务 {task_id} 的文件...")
    
    config_obj = config['default']
    FileUtils.cleanup_task_files(
        task_id,
        config_obj.UPLOAD_FOLDER,
        config_obj.TEMP_FOLDER,
        config_obj.OUTPUT_FOLDER
    )

def show_file_stats():
    """显示文件统计信息"""
    print("\n文件统计信息:")
    print("-" * 40)
    
    config_obj = config['default']
    
    for folder_name, folder_path in [
        ("上传文件夹", config_obj.UPLOAD_FOLDER),
        ("临时文件夹", config_obj.TEMP_FOLDER),
        ("输出文件夹", config_obj.OUTPUT_FOLDER)
    ]:
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            total_size = 0
            
            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            
            print(f"{folder_name}: {len(files)} 个文件, {total_size / (1024*1024):.2f} MB")
        else:
            print(f"{folder_name}: 目录不存在")

if __name__ == '__main__':
    print("压缩包转PDF工具 - 文件清理脚本")
    print("=" * 50)
    
    # 显示当前文件状态
    show_file_stats()
    
    cleanup_all_files()