# [file name]: logging_config.py
# [file content begin]
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

class JMComicLogger:
    """JM漫画下载日志系统"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = None
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建主日志记录器
        self.logger = logging.getLogger('jm_comic_downloader')
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 文件处理器 - 所有日志
            all_log_handler = RotatingFileHandler(
                os.path.join(log_dir, 'jm_comic_all.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            
            # 文件处理器 - 访问日志（专门记录IP和下载信息）
            access_log_handler = RotatingFileHandler(
                os.path.join(log_dir, 'jm_comic_access.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            
            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            access_formatter = logging.Formatter(
                '%(asctime)s - %(message)s'
            )
            
            all_log_handler.setFormatter(formatter)
            access_log_handler.setFormatter(access_formatter)
            console_handler.setFormatter(formatter)
            
            # 为访问日志设置过滤器
            class AccessLogFilter(logging.Filter):
                def filter(self, record):
                    return hasattr(record, 'log_type') and record.log_type == 'access'
            
            access_log_handler.addFilter(AccessLogFilter())
            
            # 添加处理器到日志记录器
            self.logger.addHandler(all_log_handler)
            self.logger.addHandler(access_log_handler)
            self.logger.addHandler(console_handler)
    
    def log_download_request(self, ip_address, jm_id, user_agent=None, status='started'):
        """记录下载请求"""
        try:
            # 获取客户端IP
            client_ip = self._get_client_ip(ip_address)
            
            # 记录访问日志
            access_message = f"IP: {client_ip} - JM_ID: {jm_id} - Status: {status}"
            if user_agent:
                access_message += f" - UA: {user_agent}"
                
            extra = {'log_type': 'access'}
            self.logger.info(access_message, extra=extra)
            
            # 记录详细日志
            detail_message = f"下载请求 - IP: {client_ip} - JM漫画ID: {jm_id} - 状态: {status}"
            self.logger.info(detail_message)
            
        except Exception as e:
            self.logger.error(f"记录下载请求日志失败: {str(e)}")
    
    def log_download_success(self, ip_address, jm_id, file_size=None, pdf_count=0):
        """记录下载成功"""
        try:
            client_ip = self._get_client_ip(ip_address)
            
            access_message = f"IP: {client_ip} - JM_ID: {jm_id} - Status: completed"
            if file_size:
                access_message += f" - Size: {self._format_file_size(file_size)}"
            if pdf_count > 0:
                access_message += f" - PDFs: {pdf_count}"
                
            extra = {'log_type': 'access'}
            self.logger.info(access_message, extra=extra)
            
            detail_message = f"下载成功 - IP: {client_ip} - JM漫画ID: {jm_id}"
            if file_size:
                detail_message += f" - 文件大小: {self._format_file_size(file_size)}"
            if pdf_count > 0:
                detail_message += f" - 生成PDF数量: {pdf_count}"
                
            self.logger.info(detail_message)
            
        except Exception as e:
            self.logger.error(f"记录下载成功日志失败: {str(e)}")
    
    def log_download_error(self, ip_address, jm_id, error_message):
        """记录下载错误"""
        try:
            client_ip = self._get_client_ip(ip_address)
            
            access_message = f"IP: {client_ip} - JM_ID: {jm_id} - Status: error - Error: {error_message}"
            extra = {'log_type': 'access'}
            self.logger.error(access_message, extra=extra)
            
            detail_message = f"下载错误 - IP: {client_ip} - JM漫画ID: {jm_id} - 错误: {error_message}"
            self.logger.error(detail_message)
            
        except Exception as e:
            self.logger.error(f"记录下载错误日志失败: {str(e)}")
    
    def log_system_event(self, event_type, message):
        """记录系统事件"""
        try:
            self.logger.info(f"系统事件 - 类型: {event_type} - 信息: {message}")
        except Exception as e:
            print(f"记录系统事件失败: {str(e)}")
    
    def _get_client_ip(self, request):
        """获取客户端真实IP地址"""
        try:
            if hasattr(request, 'headers'):
                # 从请求头中获取真实IP（处理反向代理情况）
                if 'X-Forwarded-For' in request.headers:
                    ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
                elif 'X-Real-IP' in request.headers:
                    ip = request.headers['X-Real-IP']
                else:
                    ip = request.remote_addr
            else:
                ip = str(request)
                
            return ip
        except Exception:
            return "unknown"
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        try:
            size_bytes = int(size_bytes)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.2f} TB"
        except:
            return "unknown"

# 创建全局日志实例
jm_logger = JMComicLogger()
# [file content end]