import os
import zipfile
import tarfile
import rarfile
import py7zr
import tempfile
from pathlib import Path
from utils.file_utils import FileUtils

class CompressionHandler:
    """压缩包处理类"""
    
    def __init__(self):
        self.extracted_files = []
        self.status_callback = None
    
    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def _update_status(self, message, progress=None):
        """更新处理状态"""
        if self.status_callback:
            self.status_callback(message, progress)
    
    def recursive_extract(self, file_path, extract_to, depth=0, max_depth=10):
        """
        递归解压压缩包
        
        Args:
            file_path: 压缩包文件路径
            extract_to: 解压目标目录
            depth: 当前递归深度
            max_depth: 最大递归深度
        
        Returns:
            list: 所有解压出的文件路径列表
        """
        if depth > max_depth:
            self._update_status(f"达到最大递归深度 {max_depth}，停止解压")
            return []
        
        self._update_status(f"开始解压: {os.path.basename(file_path)}")
        
        extracted_files = []
        
        try:
            # 根据文件类型选择解压方法
            if zipfile.is_zipfile(file_path):
                extracted_files.extend(self._extract_zip(file_path, extract_to))
            elif tarfile.is_tarfile(file_path):
                extracted_files.extend(self._extract_tar(file_path, extract_to))
            elif file_path.lower().endswith('.rar'):
                extracted_files.extend(self._extract_rar(file_path, extract_to))
            elif file_path.lower().endswith('.7z'):
                extracted_files.extend(self._extract_7z(file_path, extract_to))
            else:
                self._update_status(f"不支持的压缩格式: {file_path}")
                return []
            
            # 检查解压出的文件是否也是压缩包
            for extracted_file in extracted_files[:]:  # 使用副本进行迭代
                if FileUtils.is_compressed_file(extracted_file):
                    self._update_status(f"发现嵌套压缩包: {os.path.basename(extracted_file)}")
                    
                    # 创建子目录用于解压嵌套压缩包
                    nested_extract_to = os.path.join(
                        extract_to, 
                        f"nested_{Path(extracted_file).stem}"
                    )
                    os.makedirs(nested_extract_to, exist_ok=True)
                    
                    # 递归解压
                    nested_files = self.recursive_extract(
                        extracted_file, nested_extract_to, depth + 1, max_depth
                    )
                    extracted_files.extend(nested_files)
                    
                    # 删除已解压的嵌套压缩包文件
                    try:
                        os.remove(extracted_file)
                    except:
                        pass
            
            self._update_status(f"解压完成: {os.path.basename(file_path)}", progress=100)
            return extracted_files
            
        except Exception as e:
            self._update_status(f"解压失败 {file_path}: {str(e)}")
            return []
    
    def _extract_zip(self, file_path, extract_to):
        """解压ZIP文件"""
        extracted_files = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file_info in enumerate(file_list):
                    # 跳过目录
                    if file_info.endswith('/'):
                        continue
                    
                    # 解压文件
                    zip_ref.extract(file_info, extract_to)
                    extracted_path = os.path.join(extract_to, file_info)
                    extracted_files.append(extracted_path)
                    
                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self._update_status(f"解压ZIP文件: {file_info}", progress)
                
            return extracted_files
        except Exception as e:
            raise Exception(f"ZIP解压失败: {str(e)}")
    
    def _extract_tar(self, file_path, extract_to):
        """解压TAR文件（包括.tar.gz, .tar.bz2）"""
        extracted_files = []
        try:
            mode = 'r'
            if file_path.endswith('.gz'):
                mode = 'r:gz'
            elif file_path.endswith('.bz2'):
                mode = 'r:bz2'
            
            with tarfile.open(file_path, mode) as tar_ref:
                members = tar_ref.getmembers()
                total_files = len(members)
                
                for i, member in enumerate(members):
                    # 跳过目录
                    if member.isdir():
                        continue
                    
                    # 解压文件
                    tar_ref.extract(member, extract_to)
                    extracted_path = os.path.join(extract_to, member.name)
                    extracted_files.append(extracted_path)
                    
                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self._update_status(f"解压TAR文件: {member.name}", progress)
                
            return extracted_files
        except Exception as e:
            raise Exception(f"TAR解压失败: {str(e)}")
    
    def _extract_rar(self, file_path, extract_to):
        """解压RAR文件"""
        extracted_files = []
        try:
            with rarfile.RarFile(file_path) as rar_ref:
                file_list = rar_ref.namelist()
                total_files = len(file_list)
                
                for i, file_info in enumerate(file_list):
                    # 跳过目录
                    if file_info.endswith('/') or file_info.endswith('\\'):
                        continue
                    
                    # 解压文件
                    rar_ref.extract(file_info, extract_to)
                    extracted_path = os.path.join(extract_to, file_info)
                    extracted_files.append(extracted_path)
                    
                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self._update_status(f"解压RAR文件: {file_info}", progress)
                
            return extracted_files
        except Exception as e:
            raise Exception(f"RAR解压失败: {str(e)}")
    
    def _extract_7z(self, file_path, extract_to):
        """解压7z文件"""
        extracted_files = []
        try:
            with py7zr.SevenZipFile(file_path, mode='r') as seven_zip_ref:
                file_list = seven_zip_ref.getnames()
                total_files = len(file_list)
                
                for i, file_info in enumerate(file_list):
                    # 解压文件
                    seven_zip_ref.extract(targets=[file_info], path=extract_to)
                    extracted_path = os.path.join(extract_to, file_info)
                    extracted_files.append(extracted_path)
                    
                    # 更新进度
                    progress = (i + 1) / total_files * 100
                    self._update_status(f"解压7z文件: {file_info}", progress)
                
            return extracted_files
        except Exception as e:
            raise Exception(f"7z解压失败: {str(e)}")