# [file name]: app.py
# [file content begin]
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
from logging_config import jm_logger  # 导入日志系统
import cleanup

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
        self.jm_id = None  # 添加JM ID记录
        self.start_time = None
    
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

def process_jm_comic_task(task_id, jm_id, output_dir, client_ip):
    """处理JM漫画下载和转换的后台任务"""
    task = ProcessingTask(task_id)
    task.jm_id = jm_id
    task.start_time = threading.current_thread().ident
    
    try:
        # 更新任务状态
        task.update_status("开始下载JM漫画", 10, "下载漫画")
        
        # 使用github_action.py中的下载逻辑
        from github_action import download_jm_comic, process_comic_directly
        
        # 设置下载目录
        download_dir = 'download'
        os.makedirs(download_dir, exist_ok=True)
        
        # 下载漫画
        task.update_status("正在下载漫画", 20, "下载中")
        zip_path = download_jm_comic(jm_id, download_dir)
        
        if not zip_path:
            task.update_status("漫画下载失败", 100, "错误")
            task.error = "漫画下载失败"
            # 记录错误日志
            jm_logger.log_download_error(client_ip, jm_id, "漫画下载失败")
            return
            
        task.update_status("漫画下载完成", 40, "下载完成")
        
        # 处理漫画
        task.update_status("开始处理漫画", 50, "处理中")
        success = process_comic_directly(jm_id, zip_path, download_dir)
        
        if success:
            # 查找生成的PDF文件
            pdf_files = []
            total_size = 0
            for file in os.listdir(download_dir):
                if file.endswith('.pdf') and f"jm_{jm_id}" in file:
                    file_path = os.path.join(download_dir, file)
                    pdf_files.append(file_path)
                    total_size += os.path.getsize(file_path)
            
            if pdf_files:
                # 如果只有一个PDF，直接作为结果
                if len(pdf_files) == 1:
                    task.result_files = [pdf_files[0]]
                    processing_results[task_id] = {
                        'pdf_files': pdf_files,
                        'zip_file': pdf_files[0]  # 单个文件也作为zip_file返回
                    }
                else:
                    # 多个PDF文件，打包成ZIP
                    import zipfile
                    zip_path = os.path.join(output_dir, f"jm_{jm_id}_result.zip")
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for pdf_file in pdf_files:
                            zipf.write(pdf_file, os.path.basename(pdf_file))
                    
                    task.result_files = [zip_path]
                    processing_results[task_id] = {
                        'pdf_files': pdf_files,
                        'zip_file': zip_path
                    }
                
                task.update_status("处理完成", 100, "完成")
                # 记录成功日志
                jm_logger.log_download_success(client_ip, jm_id, total_size, len(pdf_files))
            else:
                task.update_status("未找到生成的PDF文件", 100, "错误")
                task.error = "未找到生成的PDF文件"
                jm_logger.log_download_error(client_ip, jm_id, "未找到生成的PDF文件")
        else:
            task.update_status("漫画处理失败", 100, "错误")
            task.error = "漫画处理失败"
            jm_logger.log_download_error(client_ip, jm_id, "漫画处理失败")
            
    except Exception as e:
        error_msg = str(e)
        task.update_status(f"处理失败: {error_msg}", 100, "错误")
        task.error = error_msg
        # 记录异常日志
        jm_logger.log_download_error(client_ip, jm_id, error_msg)
        import traceback
        traceback.print_exc()

@app.route('/')
def index():
    """主页"""
    # 记录页面访问
    jm_logger.log_system_event('page_access', f"主页访问 - IP: {jm_logger._get_client_ip(request)}")
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
        
        # 记录文件上传日志
        client_ip = jm_logger._get_client_ip(request)
        jm_logger.log_system_event('file_upload', 
                                  f"IP: {client_ip} - 文件: {filename} - 大小: {file_size}MB")
        
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
        jm_logger.log_system_event('upload_error', f"上传失败: {str(e)}")
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
            pdf_files = result.get('pdf_files', [])
            status_info['pdf_count'] = len(pdf_files)
            status_info['file_count'] = len(pdf_files)  # 添加文件数量
            status_info['pdf_list_url'] = f'/download/list/{task_id}'

        return jsonify(status_info)
    else:
        return jsonify({
            'status': '等待开始',
            'progress': 0,
            'current_step': '任务初始化中',
            'error': None,
            'file_count': 0
        })

@app.route('/download/<task_id>')
def download_result(task_id):
    """下载处理结果（ZIP包）"""
    if task_id in processing_results:
        result = processing_results[task_id]
        zip_file = result.get('zip_file')
        
        if zip_file and os.path.exists(zip_file):
            filename = f"converted_pdfs_{task_id}.zip"
            
            # 记录下载日志
            client_ip = jm_logger._get_client_ip(request)
            jm_logger.log_system_event('file_download', 
                                      f"IP: {client_ip} - 文件: {filename}")
            
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
                
                # 记录PDF下载日志
                client_ip = jm_logger._get_client_ip(request)
                jm_logger.log_system_event('pdf_download', 
                                          f"IP: {client_ip} - PDF文件: {filename}")
                
                return send_file(pdf_file, as_attachment=True, download_name=filename)
    
    return jsonify({'error': 'PDF文件不存在'}), 404

@app.route('/preview/pdf/<task_id>/<int:pdf_index>')
def preview_single_pdf(task_id, pdf_index):
    """预览单个PDF文件（内嵌显示）"""
    if task_id in processing_results:
        result = processing_results[task_id]
        pdf_files = result.get('pdf_files', [])
        
        if 0 <= pdf_index < len(pdf_files):
            pdf_file = pdf_files[pdf_index]
            if os.path.exists(pdf_file):
                # 设置正确的MIME类型和内嵌显示头信息
                response = send_file(pdf_file)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf_file)}"'
                return response
    
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
                    'download_url': f'/download/pdf/{task_id}/{i}',
                    'preview_url': f'/preview/pdf/{task_id}/{i}'  # 添加预览URL
                }
                file_list.append(file_info)
        
        return jsonify({'pdf_files': file_list})
    
    return jsonify({'error': '任务不存在'}), 404

@app.route('/download_jm', methods=['POST'])
def download_jm_comic():
    """JM漫画下载接口"""
    try:
        data = request.get_json()
        jm_id = data.get('jm_id')
        
        if not jm_id:
            return jsonify({'error': '缺少JM漫画ID'}), 400
        
        # 验证JM ID格式
        if not jm_id.isdigit():
            return jsonify({'error': 'JM漫画ID必须是数字'}), 400
            
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 获取客户端信息
        client_ip = jm_logger._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # 记录下载请求
        jm_logger.log_download_request(client_ip, jm_id, user_agent, 'started')
        
        # 立即创建任务状态记录，避免"任务不存在"错误
        processing_status[task_id] = {
            'status': '开始下载',
            'progress': 0,
            'current_step': '初始化',
            'error': None
        }
        
        # 启动后台处理任务
        output_dir = app.config['OUTPUT_FOLDER']
        thread = threading.Thread(
            target=process_jm_comic_task,
            args=(task_id, jm_id, output_dir, client_ip)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id, 
            'message': '开始下载JM漫画',
            'status': '开始下载'
        })
        
    except Exception as e:
        # 记录下载错误
        client_ip = jm_logger._get_client_ip(request)
        jm_id = data.get('jm_id', 'unknown') if 'data' in locals() else 'unknown'
        jm_logger.log_download_error(client_ip, jm_id, f"下载接口错误: {str(e)}")
        
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@app.route('/logs/access')
def view_access_logs():
    """查看访问日志（需要认证）"""
    try:
        # 这里可以添加认证逻辑
        log_file = 'logs/jm_comic_access.log'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            # 返回最新的100条日志
            return jsonify({'logs': logs[-100:]})
        else:
            return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': f'读取日志失败: {str(e)}'}), 500

@app.route('/logs/stats')
def get_log_stats():
    """获取日志统计信息"""
    try:
        # 这里可以添加认证逻辑
        log_file = 'logs/jm_comic_access.log'
        stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'unique_ips': set(),
            'popular_jm_ids': {}
        }
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'JM_ID:' in line:
                        stats['total_downloads'] += 1
                        
                        # 提取IP
                        if 'IP:' in line:
                            ip = line.split('IP: ')[1].split(' -')[0]
                            stats['unique_ips'].add(ip)
                        
                        # 提取JM ID和状态
                        if 'JM_ID:' in line:
                            jm_id = line.split('JM_ID: ')[1].split(' -')[0]
                            if 'Status: completed' in line:
                                stats['successful_downloads'] += 1
                            elif 'Status: error' in line:
                                stats['failed_downloads'] += 1
                            
                            # 统计热门JM ID
                            if jm_id in stats['popular_jm_ids']:
                                stats['popular_jm_ids'][jm_id] += 1
                            else:
                                stats['popular_jm_ids'][jm_id] = 1
        
        # 转换set为list
        stats['unique_ips'] = list(stats['unique_ips'])
        # 排序热门JM ID
        stats['popular_jm_ids'] = dict(sorted(
            stats['popular_jm_ids'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])  # 只显示前10个
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

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
        
        # 记录清理操作
        jm_logger.log_system_event('cleanup', '临时文件清理完成')
        
        return jsonify({'message': '清理完成'})
    except Exception as e:
        jm_logger.log_system_event('cleanup_error', f"清理失败: {str(e)}")
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
        
        # 记录任务清理
        jm_logger.log_system_event('task_cleanup', f"任务 {task_id} 文件清理完成")
        
        return jsonify({'message': f'任务 {task_id} 文件清理完成'})
    except Exception as e:
        jm_logger.log_system_event('task_cleanup_error', f"任务 {task_id} 清理失败: {str(e)}")
        return jsonify({'error': f'清理失败: {str(e)}'}), 500

# 在 app.py 中添加以下函数和路由

import random

def generate_random_jm_id():
    """生成随机的6位数JM漫画ID"""
    return str(random.randint(100000, 999999))

@app.route('/download_random_jm', methods=['POST'])
def download_random_jm_comic():
    """随机JM漫画下载接口"""
    try:
        # 生成随机6位数JM ID
        jm_id = generate_random_jm_id()
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 获取客户端信息
        client_ip = jm_logger._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # 记录下载请求
        jm_logger.log_download_request(client_ip, jm_id, user_agent, 'random_started')
        
        # 立即创建任务状态记录
        processing_status[task_id] = {
            'status': '开始随机下载',
            'progress': 0,
            'current_step': '生成随机ID',
            'error': None,
            'jm_id': jm_id  # 保存生成的JM ID
        }
        
        # 启动后台处理任务
        output_dir = app.config['OUTPUT_FOLDER']
        thread = threading.Thread(
            target=process_jm_comic_task,
            args=(task_id, jm_id, output_dir, client_ip)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id, 
            'message': f'开始下载随机JM漫画 (ID: {jm_id})',
            'jm_id': jm_id,
            'status': '开始下载'
        })
        
    except Exception as e:
        # 记录下载错误
        client_ip = jm_logger._get_client_ip(request)
        jm_logger.log_download_error(client_ip, 'random', f"随机下载接口错误: {str(e)}")
        
        return jsonify({'error': f'随机下载失败: {str(e)}'}), 500

@app.route('/batch_download_jm', methods=['POST'])
def batch_download_jm_comic():
    """批量随机JM漫画下载接口"""
    try:
        data = request.get_json()
        count = data.get('count', 1)  # 默认下载1个
        
        # 限制最大数量
        if count > 10:
            count = 10
        
        task_ids = []
        jm_ids = []
        
        for i in range(count):
            # 生成随机6位数JM ID
            jm_id = generate_random_jm_id()
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 获取客户端信息
            client_ip = jm_logger._get_client_ip(request)
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # 记录下载请求
            jm_logger.log_download_request(client_ip, jm_id, user_agent, 'batch_random_started')
            
            # 立即创建任务状态记录
            processing_status[task_id] = {
                'status': f'开始批量下载 ({i+1}/{count})',
                'progress': 0,
                'current_step': '生成随机ID',
                'error': None,
                'jm_id': jm_id
            }
            
            # 启动后台处理任务
            output_dir = app.config['OUTPUT_FOLDER']
            thread = threading.Thread(
                target=process_jm_comic_task,
                args=(task_id, jm_id, output_dir, client_ip)
            )
            thread.daemon = True
            thread.start()
            
            task_ids.append(task_id)
            jm_ids.append(jm_id)
        
        return jsonify({
            'task_ids': task_ids, 
            'jm_ids': jm_ids,
            'message': f'开始批量下载 {count} 个随机JM漫画',
            'status': '批量下载开始'
        })
        
    except Exception as e:
        client_ip = jm_logger._get_client_ip(request)
        jm_logger.log_download_error(client_ip, 'batch_random', f"批量随机下载接口错误: {str(e)}")
        
        return jsonify({'error': f'批量随机下载失败: {str(e)}'}), 500

def main_https():
    # 启动应用 - 关键修改在这里
    app.run(
        debug=True,
        host='0.0.0.0',  # 允许所有网络接口访问
        port=8443,  # 端口号
        threaded=True,  # 启用多线程处理并发请求
        ssl_context=('cert.pem', 'key.pem')  # 启用HTTPS
    )

def main_http():
    # 启动应用 - 关键修改在这里
    app.run(
        debug=True,
        host='0.0.0.0',  # 允许所有网络接口访问
        port=8443,  # 端口号
        threaded=True,  # 启用多线程处理并发请求
    )

if __name__ == '__main__':
    cleanup.clean_files("download")
    cleanup.clean_files("outputs")
    cleanup.clean_files("temp")
    cleanup.clean_files("uploads")

    # 创建必要的目录
    FileUtils.create_directories()

    # 初始化日志系统
    jm_logger.setup_logging()
    jm_logger.log_system_event('system_start', 'JM漫画下载服务启动')

    # 启用HTTP
    main_http()

    # 启用HTTPS
    main_https()
# [file content end]