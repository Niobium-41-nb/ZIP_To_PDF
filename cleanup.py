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

def clean_files(file_path, hours_old=None, task_id=None):
    """清理指定文件夹中的内容
    
    参数:
        file_path: 要清理的文件夹路径
        hours_old: 可选，只清理指定小时数之前的文件，如果为None则清理所有文件
        task_id: 可选，如果指定则只清理与该任务相关的文件
    """
    print(f"开始清理文件夹: {file_path}...")
    
    # 检查文件夹是否存在
    if not os.path.exists(file_path):
        print(f"警告: 文件夹 {file_path} 不存在")
        return
    
    if not os.path.isdir(file_path):
        print(f"警告: {file_path} 不是一个文件夹")
        return
    
    # 根据参数选择清理方式
    if task_id:
        # 清理与指定任务相关的文件
        print(f"清理与任务 {task_id} 相关的文件...")
        config_obj = config['default']
        
        # 遍历文件夹中的所有文件和子目录
        for item in os.listdir(file_path):
            item_full_path = os.path.join(file_path, item)
            
            # 如果项目名称包含task_id，则清理它
            if str(task_id) in str(item):
                FileUtils.safe_remove(item_full_path)
    elif hours_old is not None:
        # 按时间清理旧文件
        print(f"清理 {hours_old} 小时前的文件...")
        FileUtils.cleanup_old_files(file_path, hours_old)
    else:
        # 清理所有文件
        print("清理文件夹中的所有文件...")
        for item in os.listdir(file_path):
            item_full_path = os.path.join(file_path, item)
            FileUtils.safe_remove(item_full_path)
    
    print(f"文件夹 {file_path} 清理完成！")

if __name__ == '__main__':
    print("压缩包转PDF工具 - 文件清理脚本")
    print("=" * 50)
    
    # 显示当前文件状态
    show_file_stats()
    
    # 询问用户要执行的操作
    print("\n请选择操作:")
    print("1. 清理所有临时和旧文件")
    print("2. 清理指定任务的文件")
    print("3. 仅显示文件统计")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == '1':
        cleanup_all_files()
    elif choice == '2':
        task_id = input("请输入任务ID: ").strip()
        if task_id:
            cleanup_task_files(task_id)
        else:
            print("无效的任务ID")
    elif choice == '3':
        show_file_stats()
    else:
        print("无效的选择")
    
    print("\n操作完成！")