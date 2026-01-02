import os
import uuid
import threading
import time
import urllib.parse
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
        # 清理临时文件（保留输出文件供下载）
        try:
            # 清理上传文件和临时解压目录
            FileUtils.safe_remove(file_path)  # 删除上传的原始文件
            if 'temp_dir' in locals():
                FileUtils.safe_remove(temp_dir)  # 删除临时解压目录
        except Exception as cleanup_error:
            print(f"清理临时文件失败: {cleanup_error}")

@app.route('/')
def index():
    """主页 - 功能仪表板（导航页面）"""
    return render_template('dashboard.html')

@app.route('/convert')
def convert():
    """压缩包转PDF工具页面"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """仪表板 - 功能导航页面（重定向到主页）"""
    return render_template('dashboard.html')

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

@app.route('/cleanup/task/<task_id>', methods=['POST'])
def cleanup_task_files(task_id):
    """清理指定任务的所有文件"""
    try:
        FileUtils.cleanup_task_files(
            task_id,
            app.config['UPLOAD_FOLDER'],
            app.config['TEMP_FOLDER'],
            app.config['OUTPUT_FOLDER']
        )
        return jsonify({'message': f'任务 {task_id} 文件清理完成'})
    except Exception as e:
        return jsonify({'error': f'清理失败: {str(e)}'}), 500

# JM漫画下载相关路由
jm_processing_tasks = {}
jm_processing_results = {}

@app.route('/jm')
def jm_comic_page():
    """JM漫画下载页面"""
    return render_template('jm_comic.html')

@app.route('/download/jm', methods=['POST'])
def download_jm_comic():
    """下载JM漫画接口"""
    try:
        data = request.json
        jm_id = data.get('jm_id')
        task_type = data.get('task_type', 'single')
        
        if not jm_id or not jm_id.isdigit():
            return jsonify({'error': '无效的JM漫画ID'}), 400
        
        # 生成任务ID
        task_id = f"jm_{jm_id}_{str(uuid.uuid4())[:8]}"
        
        # 保存任务信息
        jm_processing_tasks[task_id] = {
            'jm_id': jm_id,
            'status': '等待开始',
            'progress': 0,
            'current_step': '',
            'task_type': task_type,
            'start_time': time.time()
        }
        
        # 启动后台下载任务
        thread = threading.Thread(
            target=process_jm_comic_task,
            args=(task_id, jm_id, task_type)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': '开始下载JM漫画',
            'jm_id': jm_id
        })
        
    except Exception as e:
        return jsonify({'error': f'下载请求失败: {str(e)}'}), 500

@app.route('/status/jm/<task_id>')
def get_jm_status(task_id):
    """获取JM漫画下载状态"""
    if task_id in jm_processing_tasks:
        status_info = jm_processing_tasks[task_id]
        
        # 检查是否完成且有结果
        if status_info['status'] == '完成' and task_id in jm_processing_results:
            result = jm_processing_results[task_id]
            status_info['files'] = result.get('files', [])
            status_info['total_size'] = result.get('total_size', 0)
            status_info['download_url'] = f'/download/jm/result/{task_id}'
        
        return jsonify(status_info)
    else:
        return jsonify({'error': '任务不存在'}), 404

@app.route('/download/jm/result/<task_id>')
def download_jm_result(task_id):
    """下载JM漫画处理结果"""
    if task_id in jm_processing_results:
        result = jm_processing_results[task_id]
        zip_file = result.get('zip_file')
        
        if zip_file and os.path.exists(zip_file):
            filename = f"jm_comic_{task_id}.zip"
            return send_file(zip_file, as_attachment=True, download_name=filename)
    
    return jsonify({'error': '文件不存在或尚未完成'}), 404

@app.route('/download/jm/file/<task_id>/<path:filename>')
def download_jm_file(task_id, filename):
    """下载JM漫画单个文件"""
    # 解码URL编码的文件名
    decoded_filename = urllib.parse.unquote(filename)
    
    if task_id in jm_processing_results:
        result = jm_processing_results[task_id]
        files = result.get('files', [])
        
        for file_info in files:
            if file_info['filename'] == decoded_filename and os.path.exists(file_info['path']):
                return send_file(file_info['path'],
                               as_attachment=True,
                               download_name=file_info['filename'])
    
    return jsonify({'error': '文件不存在'}), 404

def process_jm_comic_task(task_id, jm_id, task_type):
    """处理JM漫画下载任务"""
    task = jm_processing_tasks[task_id]
    
    try:
        # 步骤1: 下载漫画
        task['status'] = '下载中'
        task['current_step'] = '下载漫画'
        task['progress'] = 10
        
        # 使用run.py中的下载函数，传入配置参数
        from run import download_jm_comic
        download_dir = setup_download_directory()
        
        comic_dir = os.path.join(download_dir, f"jm_{jm_id}")
        os.makedirs(comic_dir, exist_ok=True)
        
        task['current_step'] = f'下载漫画 {jm_id}'
        task['progress'] = 20
        
        # 调用下载函数，使用配置中的重试次数
        max_retry = app.config.get('JM_MAX_RETRY', 3)
        zip_path = download_jm_comic(jm_id, download_dir, max_retry=max_retry)
        
        if not zip_path or not os.path.exists(zip_path):
            task['status'] = '失败'
            task['error'] = '漫画下载失败'
            return
        
        task['progress'] = 40
        task['current_step'] = '下载完成，开始处理'
        
        # 步骤2: 处理为PDF
        from utils.compression import CompressionHandler
        from utils.image_processor import ImageProcessor
        from utils.pdf_generator import PDFGenerator
        
        temp_dir = os.path.join(app.config['TEMP_FOLDER'], f"jm_temp_{task_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 解压
        task['current_step'] = '解压文件'
        task['progress'] = 50
        
        compression_handler = CompressionHandler()
        extracted_files = compression_handler._extract_zip(zip_path, temp_dir)
        
        if not extracted_files:
            task['status'] = '失败'
            task['error'] = '解压失败'
            return
        
        # 收集图片
        task['current_step'] = '处理图片'
        task['progress'] = 60
        
        image_processor = ImageProcessor()
        image_groups = image_processor.collect_and_sort_images(temp_dir)
        
        if not image_groups:
            task['status'] = '失败'
            task['error'] = '没有找到图片文件'
            return
        
        # 生成PDF
        task['current_step'] = '生成PDF'
        task['progress'] = 70
        
        pdf_generator = PDFGenerator()
        output_dir = os.path.join(download_dir, f"output_{task_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        generated_pdfs = pdf_generator.generate_pdfs_by_folder(
            image_groups,
            output_dir,
            base_name=f"jm_{jm_id}"
        )
        
        task['progress'] = 80
        
        # 打包结果
        task['current_step'] = '打包结果'
        
        if generated_pdfs:
            # 创建ZIP包
            zip_output_path = os.path.join(download_dir, f"jm_{jm_id}_result.zip")
            
            if pdf_generator.create_pdf_package(list(generated_pdfs.values()), zip_output_path):
                task['status'] = '完成'
                task['progress'] = 100
                task['current_step'] = '处理完成'
                
                # 存储结果
                result_files = []
                for pdf_path in generated_pdfs.values():
                    if os.path.exists(pdf_path):
                        result_files.append({
                            'filename': os.path.basename(pdf_path),
                            'path': pdf_path,
                            'size': os.path.getsize(pdf_path),
                            'download_url': f'/download/jm/file/{task_id}/{urllib.parse.quote(os.path.basename(pdf_path))}'
                        })
                
                jm_processing_results[task_id] = {
                    'files': result_files,
                    'zip_file': zip_output_path,
                    'total_size': sum(f['size'] for f in result_files)
                }
                
                # 清理临时文件
                try:
                    os.remove(zip_path)
                    if os.path.exists(temp_dir):
                        import shutil
                        shutil.rmtree(temp_dir)
                except:
                    pass
                
                return
        
        task['status'] = '失败'
        task['error'] = 'PDF生成失败'
        
    except Exception as e:
        task['status'] = '失败'
        task['error'] = str(e)
        import traceback
        traceback.print_exc()
    finally:
        # 更新最终状态
        jm_processing_tasks[task_id] = task

def setup_download_directory():
    """设置下载目录"""
    download_dir = os.path.join(os.getcwd(), 'download')
    os.makedirs(download_dir, exist_ok=True)
    return download_dir

def process_jm_batch_task(batch_id, jm_ids):
    """处理JM漫画批量下载任务"""
    batch_tasks = {}
    batch_results = {}
    
    try:
        # 初始化批量任务状态
        for jm_id in jm_ids:
            task_id = f"jm_{jm_id}_{str(uuid.uuid4())[:8]}"
            batch_tasks[task_id] = {
                'jm_id': jm_id,
                'status': '等待开始',
                'progress': 0,
                'current_step': '',
                'start_time': time.time()
            }
        
        # 存储批量任务信息
        jm_processing_tasks[batch_id] = {
            'batch_id': batch_id,
            'jm_ids': jm_ids,
            'total': len(jm_ids),
            'completed': 0,
            'failed': 0,
            'status': '处理中',
            'progress': 0,
            'tasks': batch_tasks
        }
        
        # 处理每个漫画
        for task_id, task_info in batch_tasks.items():
            jm_id = task_info['jm_id']
            
            # 更新任务状态
            task_info['status'] = '下载中'
            task_info['current_step'] = f'下载漫画 {jm_id}'
            task_info['progress'] = 10
            
            # 调用单个下载任务
            try:
                from run import download_jm_comic
                download_dir = setup_download_directory()
                
                # 下载漫画
                zip_path = download_jm_comic(jm_id, download_dir)
                
                if not zip_path or not os.path.exists(zip_path):
                    task_info['status'] = '失败'
                    task_info['error'] = '漫画下载失败'
                    jm_processing_tasks[batch_id]['failed'] += 1
                    continue
                
                task_info['progress'] = 40
                task_info['current_step'] = '下载完成，开始处理'
                
                # 处理为PDF
                from utils.compression import CompressionHandler
                from utils.image_processor import ImageProcessor
                from utils.pdf_generator import PDFGenerator
                
                temp_dir = os.path.join(app.config['TEMP_FOLDER'], f"jm_temp_{task_id}")
                os.makedirs(temp_dir, exist_ok=True)
                
                # 解压
                task_info['current_step'] = '解压文件'
                task_info['progress'] = 50
                
                compression_handler = CompressionHandler()
                extracted_files = compression_handler._extract_zip(zip_path, temp_dir)
                
                if not extracted_files:
                    task_info['status'] = '失败'
                    task_info['error'] = '解压失败'
                    jm_processing_tasks[batch_id]['failed'] += 1
                    continue
                
                # 收集图片
                task_info['current_step'] = '处理图片'
                task_info['progress'] = 60
                
                image_processor = ImageProcessor()
                image_groups = image_processor.collect_and_sort_images(temp_dir)
                
                if not image_groups:
                    task_info['status'] = '失败'
                    task_info['error'] = '没有找到图片文件'
                    jm_processing_tasks[batch_id]['failed'] += 1
                    continue
                
                # 生成PDF
                task_info['current_step'] = '生成PDF'
                task_info['progress'] = 70
                
                pdf_generator = PDFGenerator()
                output_dir = os.path.join(download_dir, f"output_{task_id}")
                os.makedirs(output_dir, exist_ok=True)
                
                generated_pdfs = pdf_generator.generate_pdfs_by_folder(
                    image_groups,
                    output_dir,
                    base_name=f"jm_{jm_id}"
                )
                
                task_info['progress'] = 80
                
                # 打包结果
                task_info['current_step'] = '打包结果'
                
                if generated_pdfs:
                    # 创建ZIP包
                    zip_output_path = os.path.join(download_dir, f"jm_{jm_id}_result.zip")
                    
                    if pdf_generator.create_pdf_package(list(generated_pdfs.values()), zip_output_path):
                        task_info['status'] = '完成'
                        task_info['progress'] = 100
                        task_info['current_step'] = '处理完成'
                        
                        # 存储结果
                        result_files = []
                        for pdf_path in generated_pdfs.values():
                            if os.path.exists(pdf_path):
                                result_files.append({
                                    'filename': os.path.basename(pdf_path),
                                    'path': pdf_path,
                                    'size': os.path.getsize(pdf_path),
                                    'download_url': f'/download/jm/file/{task_id}/{urllib.parse.quote(os.path.basename(pdf_path))}'
                                })
                        
                        batch_results[task_id] = {
                            'files': result_files,
                            'zip_file': zip_output_path,
                            'total_size': sum(f['size'] for f in result_files)
                        }
                        
                        jm_processing_tasks[batch_id]['completed'] += 1
                        
                        # 清理临时文件
                        try:
                            os.remove(zip_path)
                            if os.path.exists(temp_dir):
                                import shutil
                                shutil.rmtree(temp_dir)
                        except:
                            pass
                        
                        continue
                
                task_info['status'] = '失败'
                task_info['error'] = 'PDF生成失败'
                jm_processing_tasks[batch_id]['failed'] += 1
                
            except Exception as e:
                task_info['status'] = '失败'
                task_info['error'] = str(e)
                jm_processing_tasks[batch_id]['failed'] += 1
                import traceback
                traceback.print_exc()
        
        # 更新批量任务状态
        total_tasks = len(jm_ids)
        completed_tasks = jm_processing_tasks[batch_id]['completed']
        failed_tasks = jm_processing_tasks[batch_id]['failed']
        
        if completed_tasks > 0:
            jm_processing_tasks[batch_id]['status'] = '部分完成'
            jm_processing_tasks[batch_id]['progress'] = int((completed_tasks / total_tasks) * 100)
        else:
            jm_processing_tasks[batch_id]['status'] = '全部失败'
            jm_processing_tasks[batch_id]['progress'] = 0
        
        # 存储批量结果
        jm_processing_results[batch_id] = {
            'batch_id': batch_id,
            'total': total_tasks,
            'completed': completed_tasks,
            'failed': failed_tasks,
            'results': batch_results
        }
        
    except Exception as e:
        if batch_id in jm_processing_tasks:
            jm_processing_tasks[batch_id]['status'] = '失败'
            jm_processing_tasks[batch_id]['error'] = str(e)
        import traceback
        traceback.print_exc()

# 批量任务处理
@app.route('/download/jm/batch', methods=['POST'])
def download_jm_batch():
    """批量下载JM漫画"""
    try:
        data = request.json
        jm_ids = data.get('jm_ids', [])
        
        if not jm_ids:
            return jsonify({'error': '未提供漫画ID列表'}), 400
        
        # 验证ID格式
        invalid_ids = [id for id in jm_ids if not id.isdigit()]
        if invalid_ids:
            return jsonify({'error': f'无效的漫画ID: {", ".join(invalid_ids)}'}), 400
        
        # 创建批量任务
        batch_id = f"batch_{str(uuid.uuid4())[:8]}"
        
        # 启动批量处理
        thread = threading.Thread(
            target=process_jm_batch_task,
            args=(batch_id, jm_ids)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'batch_id': batch_id,
            'message': f'开始批量下载 {len(jm_ids)} 个漫画',
            'total': len(jm_ids)
        })
        
    except Exception as e:
        return jsonify({'error': f'批量下载失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 创建必要的目录
    FileUtils.create_directories()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5000)