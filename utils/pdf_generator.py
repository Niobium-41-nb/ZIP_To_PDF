import os
import img2pdf
from pathlib import Path
from utils.file_utils import FileUtils

class PDFGenerator:
    """PDF生成类"""
    
    def __init__(self):
        self.status_callback = None
    
    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def _update_status(self, message, progress=None):
        """更新处理状态"""
        if self.status_callback:
            self.status_callback(message, progress)
    
    def generate_pdf_from_images(self, image_paths, output_pdf_path, page_size='A4'):
        """
        从图片列表生成PDF
        
        Args:
            image_paths: 图片路径列表
            output_pdf_path: 输出PDF路径
            page_size: 页面尺寸
            
        Returns:
            bool: 是否成功生成
        """
        try:
            if not image_paths:
                self._update_status("没有图片可生成PDF")
                return False
            
            self._update_status(f"开始生成PDF: {Path(output_pdf_path).name}")
            
            # 验证所有图片文件都存在
            valid_images = []
            for img_path in image_paths:
                if os.path.exists(img_path):
                    valid_images.append(img_path)
                else:
                    self._update_status(f"图片文件不存在: {img_path}")
            
            if not valid_images:
                self._update_status("没有有效的图片文件")
                return False
            
            # 设置PDF页面参数
            pdf_layout_fun = self._get_pdf_layout_function(page_size)
            
            # 生成PDF
            with open(output_pdf_path, "wb") as pdf_file:
                pdf_file.write(img2pdf.convert(
                    valid_images,
                    layout_fun=pdf_layout_fun
                ))
            
            # 验证生成的PDF文件
            if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0:
                self._update_status(f"PDF生成成功: {Path(output_pdf_path).name}")
                return True
            else:
                self._update_status("PDF文件生成失败")
                return False
                
        except Exception as e:
            self._update_status(f"PDF生成失败: {str(e)}")
            return False
    
    def _get_pdf_layout_function(self, page_size):
        """获取PDF布局函数"""
        if page_size.upper() == 'A4':
            # A4尺寸：210mm x 297mm
            return img2pdf.get_layout_fun((img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297)))
        elif page_size.upper() == 'LETTER':
            # Letter尺寸：215.9mm x 279.4mm
            return img2pdf.get_layout_fun((img2pdf.mm_to_pt(215.9), img2pdf.mm_to_pt(279.4)))
        else:
            # 默认使用A4
            return img2pdf.get_layout_fun((img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297)))
    
    def generate_pdfs_by_folder(self, image_groups, output_dir, base_name="output"):
        """
        按文件夹分组生成多个PDF
        
        Args:
            image_groups: 按文件夹分组的图片字典 {folder_path: [image_paths]}
            output_dir: 输出目录
            base_name: 基础文件名
            
        Returns:
            dict: 生成的PDF文件路径字典 {folder_name: pdf_path}
        """
        generated_pdfs = {}
        total_groups = len(image_groups)
        
        for i, (folder_path, image_paths) in enumerate(image_groups.items()):
            # 更新进度
            progress = (i + 1) / total_groups * 100
            folder_name = Path(folder_path).name or "root"
            self._update_status(f"生成PDF: {folder_name}", progress)
            
            # 生成PDF文件名
            pdf_filename = f"{base_name}_{folder_name}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            # 生成PDF
            if self.generate_pdf_from_images(image_paths, pdf_path):
                generated_pdfs[folder_name] = pdf_path
        
        return generated_pdfs
    
    def create_pdf_package(self, pdf_files, output_zip_path):
        """
        将多个PDF文件打包成ZIP文件
        
        Args:
            pdf_files: PDF文件路径列表
            output_zip_path: 输出ZIP文件路径
            
        Returns:
            bool: 是否成功打包
        """
        import zipfile
        
        try:
            self._update_status("正在打包PDF文件...")
            
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for pdf_path in pdf_files:
                    if os.path.exists(pdf_path):
                        # 使用相对路径存储
                        arcname = Path(pdf_path).name
                        zipf.write(pdf_path, arcname)
            
            # 验证生成的ZIP文件
            if os.path.exists(output_zip_path) and os.path.getsize(output_zip_path) > 0:
                self._update_status(f"PDF打包成功: {Path(output_zip_path).name}")
                return True
            else:
                self._update_status("PDF打包失败")
                return False
                
        except Exception as e:
            self._update_status(f"PDF打包失败: {str(e)}")
            return False
    
    def get_pdf_info(self, pdf_path):
        """
        获取PDF文件信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            dict: PDF信息字典
        """
        try:
            file_size = os.path.getsize(pdf_path)
            file_size_mb = file_size / (1024 * 1024)
            
            return {
                'filename': Path(pdf_path).name,
                'file_size': file_size,
                'file_size_mb': round(file_size_mb, 2),
                'created_time': os.path.getctime(pdf_path)
            }
        except Exception as e:
            return {
                'filename': Path(pdf_path).name,
                'error': str(e)
            }