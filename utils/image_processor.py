import os
from pathlib import Path
from PIL import Image
from utils.file_utils import FileUtils

class ImageProcessor:
    """图片处理类"""
    
    def __init__(self):
        self.status_callback = None
    
    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def _update_status(self, message, progress=None):
        """更新处理状态"""
        if self.status_callback:
            self.status_callback(message, progress)
    
    def collect_and_sort_images(self, root_dir):
        """
        收集并排序图片文件，按文件夹分组
        
        Args:
            root_dir: 根目录路径
            
        Returns:
            dict: 按文件夹分组的图片路径字典 {folder_path: [sorted_image_paths]}
        """
        self._update_status("开始收集图片文件...")
        
        image_groups = {}
        
        # 遍历目录结构
        for root, dirs, files in os.walk(root_dir):
            image_files = []
            
            # 过滤图片文件
            for file in files:
                file_path = os.path.join(root, file)
                if FileUtils.is_image_file(file_path):
                    image_files.append(file_path)
            
            # 如果有图片文件，按自然顺序排序
            if image_files:
                # 使用自然排序
                image_files.sort(key=FileUtils.natural_sort_key)
                image_groups[root] = image_files
        
        self._update_status(f"找到 {len(image_groups)} 个包含图片的文件夹")
        return image_groups
    
    def convert_to_supported_format(self, image_path, output_dir):
        """
        将图片转换为PDF支持的格式
        
        Args:
            image_path: 原始图片路径
            output_dir: 输出目录
            
        Returns:
            str: 转换后的图片路径
        """
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 获取文件信息
                filename = Path(image_path).stem
                output_path = os.path.join(output_dir, f"{filename}.png")
                
                # 如果已经是PNG格式且不需要转换，直接返回原路径
                if image_path.lower().endswith('.png'):
                    return image_path
                
                # 转换图片格式为PNG（PDF生成最兼容的格式）
                if img.mode in ('P', 'RGBA'):
                    # 处理带透明度的图片
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # 保存为PNG格式
                img.save(output_path, 'PNG', optimize=True)
                
                return output_path
                
        except Exception as e:
            self._update_status(f"图片转换失败 {image_path}: {str(e)}")
            return None
    
    def optimize_image_for_pdf(self, image_path, max_size=(2480, 3508)):
        """
        优化图片以适应PDF页面（A4尺寸）
        
        Args:
            image_path: 图片路径
            max_size: 最大尺寸 (宽, 高)，默认A4尺寸(2480x3508像素)
            
        Returns:
            str: 优化后的图片路径
        """
        try:
            with Image.open(image_path) as img:
                # 获取原始尺寸
                original_width, original_height = img.size
                
                # 计算缩放比例
                width_ratio = max_size[0] / original_width
                height_ratio = max_size[1] / original_height
                scale_ratio = min(width_ratio, height_ratio, 1.0)  # 不超过原始尺寸
                
                # 如果不需要缩放，直接返回
                if scale_ratio >= 1.0:
                    return image_path
                
                # 计算新尺寸
                new_width = int(original_width * scale_ratio)
                new_height = int(original_height * scale_ratio)
                
                # 调整图片大小
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 保存优化后的图片（覆盖原文件）
                resized_img.save(image_path, optimize=True)
                
                self._update_status(f"优化图片尺寸: {original_width}x{original_height} -> {new_width}x{new_height}")
                return image_path
                
        except Exception as e:
            self._update_status(f"图片优化失败 {image_path}: {str(e)}")
            return image_path  # 返回原路径，不中断流程
    
    def process_image_group(self, image_group, output_dir):
        """
        处理一组图片，进行格式转换和优化
        
        Args:
            image_group: 图片路径列表
            output_dir: 输出目录
            
        Returns:
            list: 处理后的图片路径列表
        """
        processed_images = []
        total_images = len(image_group)
        
        for i, image_path in enumerate(image_group):
            # 更新进度
            progress = (i + 1) / total_images * 100
            self._update_status(f"处理图片: {Path(image_path).name}", progress)
            
            # 转换图片格式
            converted_path = self.convert_to_supported_format(image_path, output_dir)
            if converted_path:
                # 优化图片尺寸
                optimized_path = self.optimize_image_for_pdf(converted_path)
                processed_images.append(optimized_path)
            else:
                # 如果转换失败，尝试直接使用原图
                self._update_status(f"使用原图: {Path(image_path).name}")
                processed_images.append(image_path)
        
        return processed_images
    
    def get_image_info(self, image_path):
        """
        获取图片信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            dict: 图片信息字典
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'filename': Path(image_path).name
                }
        except Exception as e:
            return {
                'format': 'Unknown',
                'size': (0, 0),
                'mode': 'Unknown',
                'filename': Path(image_path).name,
                'error': str(e)
            }