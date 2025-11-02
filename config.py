import os

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB
    UPLOAD_FOLDER = 'uploads'
    TEMP_FOLDER = 'temp'
    OUTPUT_FOLDER = 'outputs'
    
    # 允许的压缩文件扩展名
    ALLOWED_EXTENSIONS = {
        'zip', 'tar', 'gz', 'bz2', 'rar', '7z', 'tar.gz', 'tar.bz2'
    }
    
    # 允许的图片文件扩展名
    ALLOWED_IMAGE_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'
    }
    
    # PDF配置
    PDF_PAGE_SIZE = 'A4'
    PDF_ORIENTATION = 'portrait'  # portrait 或 landscape
    
    # 清理配置（小时）
    CLEANUP_INTERVAL = 24  # 24小时后清理临时文件

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}