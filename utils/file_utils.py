import os
import shutil
import mimetypes
from pathlib import Path
from config import config

class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def allowed_file(filename, allowed_extensions):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def get_file_type(file_path):
        """使用mimetypes检测文件类型"""
        try:
            # 使用mimetypes库检测文件类型
            file_type, encoding = mimetypes.guess_type(file_path)
            return file_type
        except Exception as e:
            print(f"检测文件类型失败: {e}")
            return None
    
    @staticmethod
    def is_compressed_file(file_path):
        """检查是否为压缩文件"""
        file_type = FileUtils.get_file_type(file_path)
        if file_type:
            return any(compressed_type in file_type for compressed_type in [
                'application/zip',
                'application/x-tar',
                'application/gzip',
                'application/x-bzip2',
                'application/x-rar',
                'application/x-7z-compressed'
            ])
        return False
    
    @staticmethod
    def is_image_file(file_path):
        """检查是否为图片文件"""
        file_type = FileUtils.get_file_type(file_path)
        if file_type:
            return file_type.startswith('image/')
        # 备用检查：通过文件扩展名
        ext = Path(file_path).suffix.lower()[1:]
        return ext in config['default'].ALLOWED_IMAGE_EXTENSIONS
    
    @staticmethod
    def natural_sort_key(s):
        """自然排序键函数"""
        import re
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', str(s))]
    
    @staticmethod
    def create_directories():
        """创建必要的目录"""
        directories = [
            config['default'].UPLOAD_FOLDER,
            config['default'].TEMP_FOLDER,
            config['default'].OUTPUT_FOLDER
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def cleanup_old_files(directory, hours_old=24):
        """清理指定目录中超过指定时间的文件"""
        import time
        current_time = time.time()
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if current_time - file_time > hours_old * 3600:
                    try:
                        os.remove(file_path)
                        print(f"已清理文件: {file_path}")
                    except Exception as e:
                        print(f"清理文件失败 {file_path}: {e}")
    
    @staticmethod
    def get_file_size(file_path):
        """获取文件大小（MB）"""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)  # 转换为MB
        except OSError:
            return 0
    
    @staticmethod
    def safe_remove(path):
        """安全删除文件或目录"""
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"删除失败 {path}: {e}")