@echo off
echo ========================================
echo JM-tag.zip_to_PDF Docker 部署脚本
echo ========================================
echo.

REM 检查Docker是否安装
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Docker。请先安装Docker Desktop。
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM 检查Docker Compose是否可用
docker-compose --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [警告] Docker Compose可能未安装，尝试使用Docker Desktop内置版本...
)

echo 1. 检查Docker服务状态...
docker version >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] Docker服务未运行。请启动Docker Desktop。
    pause
    exit /b 1
)

echo 2. 构建Docker镜像...
echo 这可能需要几分钟时间，请耐心等待...
docker-compose build

if %errorlevel% neq 0 (
    echo [错误] 构建失败！
    pause
    exit /b 1
)

echo 3. 启动服务...
docker-compose up -d

if %errorlevel% neq 0 (
    echo [错误] 启动失败！
    pause
    exit /b 1
)

echo 4. 检查服务状态...
timeout /t 5 /nobreak >nul

docker-compose ps

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 访问地址: https://localhost:8443
echo HTTP地址: http://localhost:5000
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
echo 注意: 由于使用自签名证书，浏览器可能会显示安全警告。
echo       可以点击"高级"->"继续前往"来访问。
echo ========================================
echo.
pause