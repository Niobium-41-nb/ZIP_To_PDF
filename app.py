import os
import uuid
import threading
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from config import config
from utils.file_utils import FileUtils
from utils.compression import CompressionHandler
from utils.image_processor import ImageProcessor
from utils.pdf_generator import PDFGenerator

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(config['default'])

# 全局变量存储处理状态
processing_status = {}
processing_results = {}

class ProcessingTask:
    """处理任务类"""
    
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = "等待开始"
        self.progress = 0
        self.current_step = ""
        self.result_files = []
        self.error = None
    
    def update_status(self, status, progress=None, step=None):
        """更新任务状态"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if step:
            self.current_step = step
        
        # 更新全局状态
        processing_status[self.task_id] = {
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'error': self.error
        }

def process_compressed_file(task_id, file_path, output_dir):
    """处理压缩文件的主函数"""
    task = ProcessingTask(task_id)
    processing_status[task_id] = {
        'status': '等待开始',
        'progress': 0,
        'current_step': '',
        'error': None
    }
    
    try:
        # 步骤1: 创建临时目录
        task.update_status("创建临时目录", 5, "初始化")
        temp_dir = os.path.join(app.config['TEMP_FOLDER'], f"temp_{task_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 步骤2: 递归解压
        task.update_status("开始解压文件", 10, "解压")
        compression_handler = CompressionHandler()
        compression_handler.set_status_callback(
            lambda msg, prog=None: task.update_status(msg, prog, "解压")
        )
        
        extracted_files = compression_handler.recursive_extract(file_path, temp_dir)
        
        if not extracted_files:
            task.update_status("解压失败，没有找到文件", 100, "错误")
            task.error = "解压失败，没有找到文件"
            return
        
        task.update_status(f"解压完成，找到 {len(extracted_files)} 个文件", 30, "解压完成")
        
        # 步骤3: 收集和排序图片
        task.update_status("收集图片文件", 40, "图片处理")
        image_processor = ImageProcessor()
        image_processor.set_status_callback(
            lambda msg, prog=None: task.update_status(msg, prog, "图片处理")
        )
        
        image_groups = image_processor.collect_and_sort_images(temp_dir)
        
        if not image_groups:
            task.update_status("没有找到图片文件", 100, "错误")
            task.error = "没有找到图片文件"
            return
        
        task.update_status(f"找到 {len(image_groups)} 个包含图片的文件夹", 50, "图片收集完成")
        
        # 步骤4: 处理图片
        task.update_status("处理图片文件", 60, "图片优化")
        processed_image_groups = {}
        for folder_path, image_paths in image_groups.items():
            processed_images = image_processor.process_image_group(image_paths, temp_dir)
            processed_image_groups[folder_path] = processed_images
        
        task.update_status("图片处理完成", 70, "图片处理完成")
        
        # 步骤5: 生成PDF
        task.update_status("生成PDF文件", 80, "PDF生成")
        pdf_generator = PDFGenerator()
        pdf_generator.set_status_callback(
            lambda msg, prog=None: task.update_status(msg, prog, "PDF生成")
        )
        
        # 创建PDF输出目录
        pdf_output_dir = os.path.join(output_dir, f"pdfs_{task_id}")
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # 生成PDF
        generated_pdfs = pdf_generator.generate_pdfs_by_folder(
            processed_image_groups, 
            pdf_output_dir,
            base_name="converted"
        )
        
        if not generated_pdfs:
            task.update_status("PDF生成失败", 100, "错误")
            task.error = "PDF生成失败"
            return
        
        task.update_status(f"成功生成 {len(generated_pdfs)} 个PDF文件", 90, "PDF生成完成")
        
        # 步骤6: 打包结果
        task.update_status("打包结果文件", 95, "打包")
        zip_output_path = os.path.join(output_dir, f"result_{task_id}.zip")
        
        if pdf_generator.create_pdf_package(list(generated_pdfs.values()), zip_output_path):
            task.result_files = [zip_output_path]
            task.update_status("处理完成", 100, "完成")
        else:
            task.update_status("打包失败", 100, "错误")
            task.error = "打包失败"
        
        # 存储结果
        processing_results[task_id] = {
            'pdf_files': list(generated_pdfs.values()),
            'zip_file': zip_output_path if os.path.exists(zip_output_path) else None
        }
        
    except Exception as e:
        task.update_status(f"处理失败: {str(e)}", 100, "错误")
        task.error = str(e)
    finally:
        # 清理临时文件（在实际应用中可能需要延迟清理）
        pass

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 检查文件类型
        if not FileUtils.allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 创建必要的目录
        FileUtils.create_directories()
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
        file.save(file_path)
        
        # 检查文件大小
        file_size = FileUtils.get_file_size(file_path)
        if file_size > 1024:  # 1GB限制
            os.remove(file_path)
            return jsonify({'error': '文件大小超过1GB限制'}), 400
        
        # 启动后台处理任务
        output_dir = app.config['OUTPUT_FOLDER']
        thread = threading.Thread(
            target=process_compressed_file,
            args=(task_id, file_path, output_dir)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': '文件上传成功，开始处理'
        })
        
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/status/<task_id>')
def get_status(task_id):
    """获取处理状态"""
    if task_id in processing_status:
        status_info = processing_status[task_id]
        
        # 检查是否完成且有结果
        if status_info['status'] == '处理完成' and task_id in processing_results:
            result = processing_results[task_id]
            status_info['download_url'] = f'/download/{task_id}'
            status_info['pdf_count'] = len(result.get('pdf_files', []))
            status_info['pdf_list_url'] = f'/download/list/{task_id}'
        
        return jsonify(status_info)
    else:
        return jsonify({'error': '任务不存在'}), 404

@app.route('/download/<task_id>')
def download_result(task_id):
    """下载处理结果（ZIP包）"""
    if task_id in processing_results:
        result = processing_results[task_id]
        zip_file = result.get('zip_file')
        
        if zip_file and os.path.exists(zip_file):
            filename = f"converted_pdfs_{task_id}.zip"
            return send_file(zip_file, as_attachment=True, download_name=filename)
    
    return jsonify({'error': '文件不存在或尚未完成'}), 404

@app.route('/download/pdf/<task_id>/<int:pdf_index>')
def download_single_pdf(task_id, pdf_index):
    """下载单个PDF文件"""
    if task_id in processing_results:
        result = processing_results[task_id]
        pdf_files = result.get('pdf_files', [])
        
        if 0 <= pdf_index < len(pdf_files):
            pdf_file = pdf_files[pdf_index]
            if os.path.exists(pdf_file):
                filename = os.path.basename(pdf_file)
                return send_file(pdf_file, as_attachment=True, download_name=filename)
    
    return jsonify({'error': 'PDF文件不存在'}), 404

@app.route('/download/list/<task_id>')
def list_pdf_files(task_id):
    """获取PDF文件列表"""
    if task_id in processing_results:
        result = processing_results[task_id]
        pdf_files = result.get('pdf_files', [])
        
        file_list = []
        for i, pdf_file in enumerate(pdf_files):
            if os.path.exists(pdf_file):
                file_info = {
                    'index': i,
                    'filename': os.path.basename(pdf_file),
                    'size': os.path.getsize(pdf_file),
                    'download_url': f'/download/pdf/{task_id}/{i}'
                }
                file_list.append(file_info)
        
        return jsonify({'pdf_files': file_list})
    
    return jsonify({'error': '任务不存在'}), 404

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """清理临时文件"""
    try:
        # 清理上传文件
        FileUtils.cleanup_old_files(app.config['UPLOAD_FOLDER'])
        
        # 清理临时文件
        FileUtils.cleanup_old_files(app.config['TEMP_FOLDER'])
        
        # 清理输出文件（保留时间更长）
        FileUtils.cleanup_old_files(app.config['OUTPUT_FOLDER'], hours_old=48)
        
        return jsonify({'message': '清理完成'})
    except Exception as e:
        return jsonify({'error': f'清理失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 创建必要的目录
    FileUtils.create_directories()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5000)