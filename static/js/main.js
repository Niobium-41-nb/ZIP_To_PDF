// 主要JavaScript功能增强

class ZipToPDFApp {
    constructor() {
        this.currentTaskId = null;
        this.statusCheckInterval = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // 文件拖拽事件
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        if (uploadArea && fileInput) {
            this.setupDragAndDrop(uploadArea, fileInput);
            this.setupFileInput(fileInput);
        }

        // 清理按钮事件（如果有的话）
        const cleanupBtn = document.getElementById('cleanupBtn');
        if (cleanupBtn) {
            cleanupBtn.addEventListener('click', () => this.cleanupFiles());
        }
    }

    setupDragAndDrop(uploadArea, fileInput) {
        // 阻止默认拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // 高亮拖拽区域
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        // 处理文件放置
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        }, false);
    }

    setupFileInput(fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    async handleFile(file) {
        try {
            this.resetUI();
            
            // 验证文件
            if (!this.validateFile(file)) {
                return;
            }

            // 显示文件信息
            this.showFileInfo(file);

            // 显示进度容器
            this.showProgressContainer('正在上传文件...');

            // 上传文件
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.currentTaskId = data.task_id;
            this.showProgressContainer('文件上传成功，开始处理...');
            
            // 开始轮询状态
            this.startStatusPolling();

        } catch (error) {
            this.showError('上传失败: ' + error.message);
            console.error('File upload error:', error);
        }
    }

    validateFile(file) {
        const allowedExtensions = ['zip', 'tar', 'gz', 'bz2', 'rar', '7z', 'tar.gz', 'tar.bz2'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        const doubleExtension = file.name.split('.').slice(-2).join('.').toLowerCase();

        if (!allowedExtensions.includes(fileExtension) && !allowedExtensions.includes(doubleExtension)) {
            this.showError('不支持的文件格式。请上传ZIP、TAR、RAR或7Z格式的文件。');
            return false;
        }

        // 验证文件大小 (1GB = 1024MB)
        if (file.size > 1024 * 1024 * 1024) {
            this.showError('文件大小超过1GB限制。');
            return false;
        }

        return true;
    }

    showFileInfo(file) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        // 可以在这里添加显示文件信息的逻辑
        console.log(`文件信息: ${file.name}, 大小: ${fileSizeMB} MB`);
    }

    showProgressContainer(message) {
        const progressContainer = document.getElementById('progressContainer');
        const statusMessage = document.getElementById('statusMessage');
        
        if (progressContainer && statusMessage) {
            progressContainer.style.display = 'block';
            statusMessage.style.display = 'block';
            statusMessage.textContent = message;
        }
    }

    async startStatusPolling() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }

        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.currentTaskId}`);
                const data = await response.json();

                if (data.error) {
                    this.stopStatusPolling();
                    this.showError(data.error);
                    return;
                }

                this.updateProgress(data);

                if (data.status === '完成') {
                    this.stopStatusPolling();
                    this.showResult(data);
                } else if (data.error) {
                    this.stopStatusPolling();
                    this.showError(data.error);
                }

            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 1000);
    }

    stopStatusPolling() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    updateProgress(data) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const statusText = document.getElementById('statusText');
        const statusMessage = document.getElementById('statusMessage');

        if (progressFill) progressFill.style.width = data.progress + '%';
        if (progressText) progressText.textContent = data.progress + '%';
        if (statusText) statusText.textContent = data.current_step;
        if (statusMessage) statusMessage.textContent = data.status;
    }

    showResult(data) {
        const progressContainer = document.getElementById('progressContainer');
        const resultContainer = document.getElementById('resultContainer');
        const downloadBtn = document.getElementById('downloadBtn');

        if (progressContainer) progressContainer.style.display = 'none';
        if (resultContainer) resultContainer.style.display = 'block';

        if (downloadBtn && data.download_url) {
            downloadBtn.href = data.download_url;
            
            // 添加点击事件统计
            downloadBtn.addEventListener('click', () => {
                this.trackDownload(data.pdf_count || 1);
            });
        }

        // 显示成功消息
        this.showSuccessMessage(`成功生成 ${data.pdf_count || 1} 个PDF文件`);
    }

    showError(message) {
        const progressContainer = document.getElementById('progressContainer');
        const errorMessage = document.getElementById('errorMessage');

        if (progressContainer) progressContainer.style.display = 'none';
        if (errorMessage) {
            errorMessage.style.display = 'block';
            errorMessage.textContent = message;
        }
    }

    showSuccessMessage(message) {
        // 可以在这里添加成功消息的显示逻辑
        console.log('Success:', message);
    }

    resetUI() {
        const elements = {
            progressContainer: document.getElementById('progressContainer'),
            errorMessage: document.getElementById('errorMessage'),
            resultContainer: document.getElementById('resultContainer'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            statusText: document.getElementById('statusText')
        };

        // 隐藏所有状态容器
        if (elements.progressContainer) elements.progressContainer.style.display = 'none';
        if (elements.errorMessage) elements.errorMessage.style.display = 'none';
        if (elements.resultContainer) elements.resultContainer.style.display = 'none';

        // 重置进度
        if (elements.progressFill) elements.progressFill.style.width = '0%';
        if (elements.progressText) elements.progressText.textContent = '0%';
        if (elements.statusText) elements.statusText.textContent = '等待开始';

        // 停止轮询
        this.stopStatusPolling();
        this.currentTaskId = null;
    }

    async cleanupFiles() {
        try {
            const response = await fetch('/cleanup', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.error) {
                alert('清理失败: ' + data.error);
            } else {
                alert('临时文件清理完成');
            }
        } catch (error) {
            alert('清理请求失败: ' + error.message);
        }
    }

    trackDownload(pdfCount) {
        // 可以在这里添加下载统计逻辑
        console.log(`用户下载了 ${pdfCount} 个PDF文件`);
    }
}

// 工具函数
const Utils = {
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            return `${minutes}分${remainingSeconds}秒`;
        } else {
            return `${remainingSeconds}秒`;
        }
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.zipToPDFApp = new ZipToPDFApp();
    
    // 添加页面卸载时的清理
    window.addEventListener('beforeunload', () => {
        if (window.zipToPDFApp) {
            window.zipToPDFApp.stopStatusPolling();
        }
    });
});

// 导出供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ZipToPDFApp, Utils };
}