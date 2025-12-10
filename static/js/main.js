// 主要JavaScript功能增强

class ZipToPDFApp {
    constructor() {
        this.currentTaskId = null;
        this.statusCheckInterval = null;
        this.uploadProgressManager = new ProgressManager('');
        this.jmProgressManager = new ProgressManager('jm');
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

        // JM下载按钮事件
        const jmDownloadBtn = document.getElementById('jmDownloadBtn');
        if (jmDownloadBtn) {
            jmDownloadBtn.addEventListener('click', () => this.handleJmDownload());
        }

        // 清理按钮事件
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

            // 显示进度容器
            this.showProgressContainer('正在上传文件...');

            // 初始化进度条
            this.uploadProgressManager.start();

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
                this.uploadProgressManager.stop();
                return;
            }

            this.currentTaskId = data.task_id;

            // 开始轮询状态
            this.startStatusPolling();

        } catch (error) {
            this.showError('上传失败: ' + error.message);
            this.uploadProgressManager.stop();
            console.error('File upload error:', error);
        }
    }

    async handleJmDownload() {
        try {
            const jmIdInput = document.getElementById('jmIdInput');
            const jmId = jmIdInput.value.trim();

            if (!jmId) {
                this.showJmError('请输入JM漫画ID');
                return;
            }

            if (!/^\d+$/.test(jmId)) {
                this.showJmError('JM漫画ID必须是数字');
                return;
            }

            this.jmResetUI();

            // 显示进度容器
            this.showJmProgressContainer('开始下载JM漫画...');

            // 初始化进度条
            this.jmProgressManager.start();
            this.jmProgressManager.updateJmId(jmId);

            // 发送下载请求
            const response = await fetch('/download_jm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ jm_id: jmId })
            });

            const data = await response.json();

            if (data.error) {
                this.showJmError(data.error);
                this.jmProgressManager.stop();
                return;
            }

            this.jmCurrentTaskId = data.task_id;

            // 开始轮询状态
            this.startJmStatusPolling();

        } catch (error) {
            this.showJmError('下载失败: ' + error.message);
            this.jmProgressManager.stop();
            console.error('JM download error:', error);
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

    showProgressContainer(message) {
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
    }

    showJmProgressContainer(message) {
        const jmProgressContainer = document.getElementById('jmProgressContainer');
        if (jmProgressContainer) {
            jmProgressContainer.style.display = 'block';
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
                    this.uploadProgressManager.stop();
                    return;
                }

                // 更新进度条
                this.uploadProgressManager.updateProgress(data.progress, data.status, data.current_step);

                // 如果有文件数量信息，更新显示
                if (data.file_count) {
                    this.uploadProgressManager.updateFileCount(data.file_count);
                }

                if (data.status === '处理完成') {
                    this.stopStatusPolling();
                    this.uploadProgressManager.stop();
                    this.showResult(data);
                } else if (data.error) {
                    this.stopStatusPolling();
                    this.uploadProgressManager.stop();
                    this.showError(data.error);
                }

            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 1000);
    }

    async startJmStatusPolling() {
        if (this.jmStatusCheckInterval) {
            clearInterval(this.jmStatusCheckInterval);
        }

        let retryCount = 0;
        const maxRetries = 60;

        this.jmStatusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.jmCurrentTaskId}`);
                const data = await response.json();

                retryCount = 0; // 重置重试计数

                if (data.error) {
                    this.stopJmStatusPolling();
                    this.showJmError(data.error);
                    this.jmProgressManager.stop();
                    return;
                }

                // 更新进度条
                this.jmProgressManager.updateProgress(data.progress, data.status, data.current_step);

                if (data.status === '处理完成') {
                    this.stopJmStatusPolling();
                    this.jmProgressManager.stop();
                    this.showJmResult(data);
                } else if (data.error) {
                    this.stopJmStatusPolling();
                    this.jmProgressManager.stop();
                    this.showJmError(data.error);
                }

            } catch (error) {
                console.error('JM status check error:', error);

                if (retryCount < maxRetries) {
                    retryCount++;
                    console.log(`JM状态检查失败，重试 ${retryCount}/${maxRetries}`);
                    return;
                }

                this.stopJmStatusPolling();
                this.jmProgressManager.stop();
                this.showJmError('状态检查失败: ' + error.message);
            }
        }, 2000);
    }

    stopStatusPolling() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    stopJmStatusPolling() {
        if (this.jmStatusCheckInterval) {
            clearInterval(this.jmStatusCheckInterval);
            this.jmStatusCheckInterval = null;
        }
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

    showJmResult(data) {
        const jmProgressContainer = document.getElementById('jmProgressContainer');
        const jmResultContainer = document.getElementById('jmResultContainer');
        const jmDownloadBtnResult = document.getElementById('jmDownloadBtnResult');

        if (jmProgressContainer) jmProgressContainer.style.display = 'none';
        if (jmResultContainer) jmResultContainer.style.display = 'block';

        if (jmDownloadBtnResult && data.download_url) {
            jmDownloadBtnResult.href = data.download_url;
        }

        // 显示成功消息
        this.showJmSuccessMessage(`成功下载并转换JM漫画`);
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

    showJmError(message) {
        const jmProgressContainer = document.getElementById('jmProgressContainer');
        const jmErrorMessage = document.getElementById('jmErrorMessage');

        if (jmProgressContainer) jmProgressContainer.style.display = 'none';
        if (jmErrorMessage) {
            jmErrorMessage.style.display = 'block';
            jmErrorMessage.textContent = message;
        }
    }

    showSuccessMessage(message) {
        // 可以在这里添加成功消息的显示逻辑
        console.log('Success:', message);
    }

    showJmSuccessMessage(message) {
        // 可以在这里添加JM成功消息的显示逻辑
        console.log('JM Success:', message);
    }

    resetUI() {
        const elements = {
            progressContainer: document.getElementById('progressContainer'),
            errorMessage: document.getElementById('errorMessage'),
            resultContainer: document.getElementById('resultContainer'),
            pdfListContainer: document.getElementById('pdfListContainer')
        };

        // 隐藏所有状态容器
        Object.values(elements).forEach(element => {
            if (element) element.style.display = 'none';
        });

        // 停止轮询
        this.stopStatusPolling();
        this.currentTaskId = null;

        // 重置进度管理器
        this.uploadProgressManager.reset();
    }

    jmResetUI() {
        const elements = {
            jmProgressContainer: document.getElementById('jmProgressContainer'),
            jmErrorMessage: document.getElementById('jmErrorMessage'),
            jmResultContainer: document.getElementById('jmResultContainer'),
            jmPdfListContainer: document.getElementById('jmPdfListContainer')
        };

        // 隐藏所有状态容器
        Object.values(elements).forEach(element => {
            if (element) element.style.display = 'none';
        });

        // 停止轮询
        this.stopJmStatusPolling();
        this.jmCurrentTaskId = null;

        // 重置进度管理器
        this.jmProgressManager.reset();
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

// 进度条管理类
class ProgressManager {
    constructor(prefix = '') {
        this.prefix = prefix;
        this.startTime = null;
        this.timerInterval = null;
    }

    start() {
        this.startTime = new Date();
        this.updateStartTime();
        this.startTimer();
    }

    updateStartTime() {
        const startTimeElement = document.getElementById(`${this.prefix}StartTime`);
        if (startTimeElement) {
            startTimeElement.textContent = this.startTime.toLocaleTimeString();
        }
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            this.updateElapsedTime();
        }, 1000);
    }

    updateElapsedTime() {
        const elapsedTimeElement = document.getElementById(`${this.prefix}ElapsedTime`);
        if (elapsedTimeElement && this.startTime) {
            const now = new Date();
            const elapsed = Math.floor((now - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            elapsedTimeElement.textContent = `${minutes}分${seconds}秒`;
        }
    }

    stop() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    updateProgress(progress, status, step) {
        // 更新进度条
        const progressFill = document.getElementById(`${this.prefix}ProgressFill`);
        const progressText = document.getElementById(`${this.prefix}ProgressText`);
        const statusText = document.getElementById(`${this.prefix}StatusText`);
        const detailStatus = document.getElementById(`${this.prefix}DetailStatus`);

        if (progressFill) {
            progressFill.style.width = progress + '%';
        }
        if (progressText) {
            progressText.textContent = progress + '%';
        }
        if (statusText) {
            statusText.textContent = status;
        }
        if (detailStatus) {
            detailStatus.textContent = status;
            // 根据状态更新颜色
            detailStatus.className = 'status-value ' +
                (progress === 100 ? 'success' :
                 status.includes('错误') || status.includes('失败') ? 'error' : 'processing');
        }

        // 更新步骤指示器
        this.updateSteps(progress, step);
    }

    updateSteps(progress, currentStep) {
        const steps = [1, 2, 3, 4, 5];

        steps.forEach(stepNum => {
            const stepElement = document.getElementById(`${this.prefix}Step${stepNum}`);
            if (stepElement) {
                const stepProgress = (stepNum - 1) * 25; // 每个步骤25%

                if (progress >= 100) {
                    // 所有步骤完成
                    stepElement.classList.add('completed');
                    stepElement.classList.remove('active');
                } else if (progress >= stepProgress + 25) {
                    // 步骤已完成
                    stepElement.classList.add('completed');
                    stepElement.classList.remove('active');
                } else if (progress >= stepProgress) {
                    // 当前活跃步骤
                    stepElement.classList.add('active');
                    stepElement.classList.remove('completed');
                } else {
                    // 未开始步骤
                    stepElement.classList.remove('active', 'completed');
                }
            }
        });
    }

    updateFileCount(count) {
        const fileCountElement = document.getElementById(`${this.prefix}FileCount`);
        if (fileCountElement && count !== undefined) {
            fileCountElement.textContent = count;
        }
    }

    updateJmId(jmId) {
        const jmIdElement = document.getElementById(`${this.prefix}JmIdDisplay`);
        if (jmIdElement && jmId) {
            jmIdElement.textContent = jmId;
        }
    }

    reset() {
        this.stop();
        this.startTime = null;

        // 重置所有UI元素
        this.updateProgress(0, '等待开始', '');
        this.updateFileCount('--');

        const startTimeElement = document.getElementById(`${this.prefix}StartTime`);
        const elapsedTimeElement = document.getElementById(`${this.prefix}ElapsedTime`);
        const jmIdElement = document.getElementById(`${this.prefix}JmIdDisplay`);

        if (startTimeElement) startTimeElement.textContent = '--';
        if (elapsedTimeElement) elapsedTimeElement.textContent = '--';
        if (jmIdElement) jmIdElement.textContent = '--';

        // 重置步骤指示器
        const steps = [1, 2, 3, 4, 5];
        steps.forEach(stepNum => {
            const stepElement = document.getElementById(`${this.prefix}Step${stepNum}`);
            if (stepElement) {
                stepElement.classList.remove('active', 'completed');
            }
        });
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
            window.zipToPDFApp.stopJmStatusPolling();
        }
    });
});

// 导出供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ZipToPDFApp, Utils, ProgressManager };
}