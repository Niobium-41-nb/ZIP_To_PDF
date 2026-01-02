````markdown
# Docker 部署指南

本文档介绍如何使用 Docker 和 Docker Compose部署 JM-tag.zip_to_PDF 应用程序。

## 前提条件

1. **Docker Desktop** (Windows 11)
   - 下载地址: https://www.docker.com/products/docker-desktop/
   - 安装后确保 Docker 服务正在运行

2. **Git** (可选，用于克隆代码)
   - 下载地址: https://git-scm.com/download/win

## 快速开始

### 1. 克隆项目（如果尚未克隆）
```bash
git clone <项目地址>
cd JM-tag.zip_to_PDF
```

### 2. 构建和运行 Docker 容器

#### 方法一：使用 Docker Compose（推荐）
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 方法二：直接使用 Docker
```bash
# 构建镜像
docker build -t jm-tag-to-pdf .

# 运行容器
docker run -d \
  --name jm-tag-to-pdf \
  -p 8443:8443 \
  -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/download:/app/download \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/temp:/app/temp \
  jm-tag-to-pdf
```

### 3. 访问应用程序
- **Web界面**: https://localhost:8443
- **HTTP界面**: http://localhost:5000 (如果启用)

> **注意**: 由于使用自签名证书，浏览器可能会显示安全警告。可以点击"高级"->"继续前往"来访问。

## 配置说明

### 环境变量
可以通过环境变量配置应用程序：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_ENV` | `production` | 运行环境 |
| `SECRET_KEY` | `your-secret-key-here` | Flask 密钥 |
| `TZ` | `Asia/Shanghai` | 时区设置 |

在 `docker-compose.yml` 中设置环境变量：
```yaml
environment:
  - SECRET_KEY=your-actual-secret-key
  - FLASK_ENV=production
```

### 数据持久化
以下目录被映射到宿主机，确保数据不会丢失：

| 容器目录 | 宿主机目录 | 说明 |
|----------|------------|------|
| `/app/uploads` | `./uploads` | 上传的文件 |
| `/app/download` | `./download` | 下载的漫画 |
| `/app/outputs` | `./outputs` | 生成的PDF文件 |
| `/app/logs` | `./logs` | 应用程序日志 |
| `/app/temp` | `./temp` | 临时文件 |
````