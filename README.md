# Flask压缩包转PDF工具 + JM漫画下载器

一个基于Python Flask的Web应用，能够处理嵌套压缩包，提取其中的图片文件并转换为PDF。同时支持直接从JM漫画下载漫画并自动转换为PDF。

## 功能特性

### 🎯 核心功能
- ✅ **压缩包转PDF**: 支持ZIP, TAR, RAR, 7Z等格式，自动递归解压嵌套压缩包
- ✅ **JM漫画下载**: 直接输入JM漫画ID，自动下载并转换为PDF
- ✅ **多种图片格式**: JPG, PNG, WEBP, GIF, BMP
- ✅ **智能排序**: 按文件名自然排序，保持图片原始顺序
- ✅ **A4竖排PDF**: 生成标准A4尺寸的PDF文件

### 🚀 用户体验
- ✅ **双模式运行**: Web界面 + 命令行模式
- ✅ **实时进度显示**: 上传、解压、处理、生成全过程进度显示
- ✅ **大文件支持**: 支持最大1GB的文件
- ✅ **现代化界面**: 响应式设计，支持拖拽上传
- ✅ **灵活下载**: 支持完整包下载和单个PDF文件下载

### 🔧 系统管理
- ✅ **自动文件清理**: 处理完成后自动清理临时文件
- ✅ **GitHub Actions**: 支持云端自动处理
- ✅ **多线程处理**: 高效处理大量文件
- ✅ **错误恢复**: 完善的错误处理和重试机制

## 项目结构

```
zip_to_pdf_app/
├── app.py                    # Flask主应用
├── run.py                    # 启动脚本（支持JM漫画下载）
├── github_action.py          # GitHub Action专用脚本
├── cleanup.py                # 文件清理脚本
├── requirements.txt          # Python依赖包
├── config.py                # 配置文件
├── README.md                # 项目说明文档
├── .github/workflows/       # GitHub Actions配置
│   └── download-jm-comic.yml
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── file_utils.py        # 文件处理工具
│   ├── compression.py       # 压缩包处理
│   ├── image_processor.py   # 图片处理
│   └── pdf_generator.py     # PDF生成
├── static/
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── main.js          # 前端JavaScript
├── templates/
│   └── index.html           # 主页面模板
├── uploads/                 # 上传文件临时存储
├── temp/                    # 解压临时目录
├── outputs/                 # 生成的PDF文件
└── download/                # JM漫画下载目录
```

## 快速开始

### 方法1: Web界面（推荐）
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Web应用
python run.py --web
# 或直接运行
python app.py

# 访问 http://localhost:5000
```

### 方法2: 命令行下载JM漫画
```bash
# 下载指定JM漫画并转换为PDF
python run.py 422866

# 同时支持多个ID
python run.py 422866 422867
```

### 方法3: GitHub Actions云端处理
1. 进入GitHub仓库的 **Actions** 页面
2. 选择 **"Download JM Comic and Convert to PDF"**
3. 点击 **"Run workflow"**，输入JM漫画ID
4. 在Artifacts中下载生成的PDF文件

## 详细使用指南

### 🖥️ Web界面模式
1. **上传压缩包**: 拖拽或点击选择ZIP/RAR/7Z文件
2. **自动处理**: 系统自动解压、处理图片、生成PDF
3. **下载结果**: 
   - 📦 **完整包**: 下载包含所有PDF的ZIP文件
   - 📄 **单个文件**: 在文件列表中单独下载PDF

### ⌨️ 命令行模式
```bash
# 基本用法
python run.py <JM漫画ID>

# 示例
python run.py 422866

# 其他选项
python run.py --web          # 启动Web界面
python run.py --cleanup      # 清理下载文件
python run.py --cleanup-temp # 清理临时文件

# 交互模式（无参数运行）
python run.py
```

### ☁️ GitHub Actions模式
1. **无需本地安装**: 直接在云端处理
2. **自动打包**: 处理完成后自动生成下载链接
3. **文件保留**: Artifacts保留7天供下载
4. **使用限制**: 每个workflow最长运行6小时

## 下载选项

### 📦 完整下载包
- 包含所有PDF文件的ZIP压缩包
- 适合批量下载和存档
- 保持原始目录结构

### 📄 单个文件下载
- 按文件夹分组的独立PDF文件
- 显示文件大小和详细信息
- 支持选择性下载

## 文件管理

### 自动清理
- 🗑️ **上传文件**: 处理完成后立即删除
- 🗑️ **临时文件**: 解压后自动清理
- 🗑️ **输出文件**: 保留48小时后自动清理

### 手动清理
```bash
# 运行清理工具
python cleanup.py

# 选项:
# 1. 清理所有临时文件
# 2. 清理指定任务文件  
# 3. 显示文件统计
# 4. 清理下载文件
```

### API清理接口
- `POST /cleanup` - 清理所有临时文件
- `POST /cleanup/task/<task_id>` - 清理指定任务文件

## 技术架构

### 后端技术栈
- **Web框架**: Python Flask
- **文件处理**: zipfile, tarfile, rarfile, py7zr
- **图片处理**: Pillow (PIL)
- **PDF生成**: img2pdf
- **漫画下载**: jmcomic
- **文件检测**: python-magic

### 前端技术栈
- **界面**: HTML5, CSS3, JavaScript
- **交互**: 原生JavaScript，无框架依赖
- **样式**: 现代化渐变设计，响应式布局
- **功能**: 拖拽上传，实时进度，错误处理

## 配置说明

在 `config.py` 中可自定义：

```python
# 文件大小限制 (默认1GB)
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024

# 支持的文件格式
ALLOWED_EXTENSIONS = {'zip', 'tar', 'gz', 'bz2', 'rar', '7z'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}

# PDF设置
PDF_PAGE_SIZE = 'A4'
PDF_ORIENTATION = 'portrait'

# 清理设置
CLEANUP_INTERVAL = 24  # 小时
```

## API接口文档

### 文件处理接口
- `POST /upload` - 上传压缩包文件
- `GET /status/<task_id>` - 获取处理状态
- `GET /download/<task_id>` - 下载ZIP包
- `GET /download/list/<task_id>` - 获取PDF列表
- `GET /download/pdf/<task_id>/<pdf_index>` - 下载单个PDF

### 系统管理接口
- `POST /cleanup` - 清理临时文件
- `POST /cleanup/task/<task_id>` - 清理任务文件

## 处理流程

1. **📤 文件上传** → 验证格式和大小
2. **📂 递归解压** → 自动处理嵌套压缩包  
3. **🖼️ 图片收集** → 按文件夹分组排序
4. **⚡ 图片处理** → 格式转换和尺寸优化
5. **📄 PDF生成** → 按文件夹创建PDF
6. **📦 结果打包** → 生成下载文件
7. **⬇️ 文件下载** → 提供多种下载方式
8. **🧹 自动清理** → 清理临时文件

## 故障排除

### 常见问题解决

**🔄 文件上传失败**
```bash
# 检查文件大小
ls -lh your_file.zip

# 检查文件格式
file your_file.zip
```

**📂 解压失败**
- 确认压缩包未损坏
- 检查是否受密码保护
- 验证文件格式支持

**📄 PDF生成失败**
- 检查图片文件完整性
- 确认磁盘空间充足
- 查看控制台错误日志

**💾 磁盘空间不足**
```bash
# 清理临时文件
python run.py --cleanup-temp

# 清理下载文件  
python run.py --cleanup
```

### 日志诊断
应用运行时的详细错误信息会在控制台输出，可根据错误信息进行针对性解决。

## 系统要求

- **Python**: 3.7+ (推荐3.9+)
- **内存**: 建议4GB+
- **磁盘空间**: 至少2GB空闲空间
- **网络**: 稳定的网络连接（JM漫画下载需要）

## 许可证

MIT License

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 贡献方式
1. 🐛 **报告问题**: 提交Issue描述遇到的问题
2. 💡 **功能建议**: 提出新功能或改进建议  
3. 🔧 **代码贡献**: 提交Pull Request修复问题或添加功能
4. 📖 **文档改进**: 帮助完善使用文档和说明

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd zip_to_pdf_app

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_github_action.py
```

---

**温馨提示**: 请合理使用本工具，遵守相关法律法规，尊重版权，不要过度爬取以免对服务器造成压力。