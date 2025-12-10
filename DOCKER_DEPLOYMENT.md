# Docker 部署指南

本文档介绍如何使用 Docker 和 Docker Compose 部署 JM-tag.zip_to_PDF 应用程序。

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

### 端口映射
- `8443`: HTTPS 端口（主要访问端口）
- `5000`: HTTP 端口（备用端口）

## 高级配置

### 1. 使用自定义 SSL 证书
如果需要使用自己的 SSL 证书：

1. 将证书文件复制到项目根目录：
   - `cert.pem` (证书文件)
   - `key.pem` (私钥文件)

2. Docker 会自动使用这些证书文件。

### 2. 修改 Dockerfile
如果需要修改基础镜像或安装额外依赖，编辑 `Dockerfile`：

```dockerfile
# 修改Python版本
FROM python:3.10-slim

# 添加额外系统包
RUN apt-get update && apt-get install -y \
    your-additional-package
```

### 3. 使用 .env 文件管理配置
创建 `.env` 文件：
```bash
# .env
SECRET_KEY=your-very-secret-key
FLASK_ENV=production
TZ=Asia/Shanghai
```

在 `docker-compose.yml` 中引用：
```yaml
env_file:
  - .env
```

## 维护命令

### 常用 Docker Compose 命令
```bash
# 启动服务（后台运行）
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f jm-tag-to-pdf

# 进入容器
docker-compose exec jm-tag-to-pdf bash

# 重建镜像
docker-compose build --no-cache
```

### 常用 Docker 命令
```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 查看容器日志
docker logs -f jm-tag-to-pdf

# 停止容器
docker stop jm-tag-to-pdf

# 删除容器
docker rm jm-tag-to-pdf

# 删除镜像
docker rmi jm-tag-to-pdf

# 清理未使用的资源
docker system prune -a
```

## 故障排除

### 1. 端口冲突
如果端口 8443 或 5000 已被占用，修改 `docker-compose.yml`：
```yaml
ports:
  - "8444:8443"  # 将宿主机端口改为 8444
```

### 2. 权限问题
在 Windows 上，可能需要为 Docker 共享驱动器：
1. 打开 Docker Desktop
2. 进入 Settings -> Resources -> File Sharing
3. 添加项目所在目录

### 3. 容器启动失败
检查日志：
```bash
docker-compose logs jm-tag-to-pdf
```

常见问题：
- 缺少依赖：确保 `requirements.txt` 完整
- 目录权限：确保映射的目录存在且有适当权限
- 内存不足：Docker Desktop 默认内存可能不足，增加内存分配

### 4. SSL 证书问题
如果遇到 SSL 证书错误：
1. 检查证书文件是否存在
2. 重新生成证书：
   ```bash
   # 在容器内执行
   docker-compose exec jm-tag-to-pdf bash
   cd /app
   rm -f cert.pem key.pem
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
     -days 365 -nodes -subj "/C=CN/ST=Beijing/L=Beijing/O=JM Comic/CN=localhost"
   exit
   docker-compose restart
   ```

## 性能优化

### 1. 使用 .dockerignore
创建 `.dockerignore` 文件排除不必要的文件：
```
.git
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.venv
.env
*.log
*.tmp
*.temp
.DS_Store
```

### 2. 多阶段构建（可选）
对于生产环境，可以使用多阶段构建减小镜像大小：
```dockerfile
# 构建阶段
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
# ... 其余配置
```

## 更新应用程序

### 1. 更新代码后重新部署
```bash
# 拉取最新代码
git pull

# 重建并重启
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. 仅更新依赖
```bash
# 修改 requirements.txt 后
docker-compose build --no-cache jm-tag-to-pdf
docker-compose up -d
```

## 备份和恢复

### 备份数据
```bash
# 备份所有数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz uploads download outputs logs temp
```

### 恢复数据
```bash
# 解压备份
tar -xzf backup-20231210.tar.gz

# 确保目录存在
mkdir -p uploads download outputs logs temp

# 启动服务
docker-compose up -d
```

## 支持

如有问题，请检查：
1. Docker Desktop 是否正常运行
2. 查看应用程序日志：`docker-compose logs -f`
3. 确保防火墙允许相关端口

如需进一步帮助，请提供：
- Docker 版本：`docker --version`
- Docker Compose 版本：`docker-compose --version`
- 错误日志：`docker-compose logs jm-tag-to-pdf`