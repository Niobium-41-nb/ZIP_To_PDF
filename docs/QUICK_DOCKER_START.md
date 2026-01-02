````markdown
# Docker 快速启动指南

本指南将帮助您快速使用 Docker 部署 JM-tag.zip_to_PDF 应用程序。

## 一分钟快速启动

### Windows 用户（最简单的方式）
1. **双击运行** `deploy.bat`
2. **等待构建完成**（首次运行需要几分钟）
3. **访问** https://localhost:8443

### 所有平台通用命令
```bash
# 1. 构建并启动服务
docker-compose up -d

# 2. 查看服务状态
docker-compose ps

# 3. 查看实时日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

## 详细步骤

### 步骤1：准备工作
确保已安装：
- ✅ **Docker Desktop** (Windows/Mac) 或 **Docker Engine** (Linux)
- ✅ **Git** (可选，用于克隆代码)

### 步骤2：获取代码
```bash
# 如果您已经在本目录，跳过此步
# 否则克隆或下载项目代码
```

### 步骤3：部署应用
```bash
# 进入项目目录
cd JM-tag.zip_to_PDF

# 方法A：使用Docker Compose（推荐）
docker-compose up -d

# 方法B：使用部署脚本
# Windows: 双击 deploy.bat
# PowerShell: .\deploy.ps1 deploy

# 方法C：手动构建和运行
docker build -t jm-tag-to-pdf .
docker run -d -p 8443:8443 -p 5000:5000 --name jm-tag-to-pdf jm-tag-to-pdf
```

### 步骤4：访问应用
- **主界面**: https://localhost:8443
- **备用地址**: http://localhost:5000

> **注意**: 由于使用自签名证书，浏览器会显示安全警告。点击"高级"→"继续前往"即可。

### 步骤5：验证部署
```bash
# 检查容器状态
docker-compose ps

# 应该看到类似输出：
# NAME                COMMAND                  SERVICE             STATUS              PORTS
# jm-tag-to-pdf       "python run.py --web"   jm-tag-to-pdf        running             0.0.0.0:5000->5000/tcp, 0.0.0.0:8443->8443/tcp

# 检查应用健康状态
curl http://localhost:5000
```

## 常用命令

### 服务管理
```bash
# 启动服务
docker-compose start

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec jm-tag-to-pdf bash
```

### 数据管理
```bash
# 备份数据
docker-compose exec jm-tag-to-pdf tar -czf /tmp/backup.tar.gz /app/uploads /app/download /app/outputs

# 清理临时文件
docker-compose exec jm-tag-to-pdf python cleanup.py

# 查看磁盘使用
docker-compose exec jm-tag-to-pdf df -h
```

### 更新应用
```bash
# 1. 停止服务
docker-compose down

# 2. 拉取最新代码（如果有）
git pull

# 3. 重建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d
```

## 故障排除

### 1. 端口冲突
如果端口 8443 或 5000 已被占用：
```yaml
# 修改 docker-compose.yml 中的 ports 部分
ports:
  - "8444:8443"  # 改为其他端口
  - "5001:5000"
```

### 2. 构建失败
```bash
# 清理缓存重新构建
docker-compose build --no-cache --pull

# 或者单独构建
docker build --no-cache -t jm-tag-to-pdf .
```

### 3. 容器启动失败
```bash
# 查看详细日志
docker-compose logs jm-tag-to-pdf

# 常见问题：
# - 缺少依赖：检查 requirements.txt
# - 权限问题：确保目录可写
# - 内存不足：增加Docker内存分配
```

### 4. 无法访问应用
```bash
# 检查容器是否运行
docker-compose ps

# 检查端口映射
docker-compose port jm-tag-to-pdf 8443

# 检查防火墙设置
# Windows: 检查Windows Defender防火墙
# Mac/Linux: 检查iptables/ufw设置
```

## 数据持久化

您的数据保存在以下目录中，即使容器重启也不会丢失：

| 目录 | 说明 | 容器内路径 | 宿主机路径 |
|------|------|------------|------------|
| uploads | 上传的文件 | /app/uploads | ./uploads |
| download | 下载的漫画 | /app/download | ./download |
| outputs | 生成的PDF | /app/outputs | ./outputs |
| logs | 应用程序日志 | /app/logs | ./logs |
| temp | 临时文件 | /app/temp | ./temp |

## 性能优化

### 调整Docker资源
1. 打开 Docker Desktop
2. 进入 Settings → Resources
3. 调整：
   - **CPU**: 建议4核以上
   - **内存**: 建议4GB以上
   - **Swap**: 1GB以上

### 使用生产环境配置
创建 `.env` 文件：
```bash
# .env
SECRET_KEY=your-very-secure-secret-key
FLASK_ENV=production
TZ=Asia/Shanghai
```

````