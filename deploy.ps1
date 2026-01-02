# JM-tag.zip_to_PDF Docker 部署脚本 (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JM-tag.zip_to_PDF Docker 部署脚本" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否安装
function Test-Docker {
    try {
        $null = Get-Command docker -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Test-DockerCompose {
    try {
        $null = Get-Command docker-compose -ErrorAction Stop
        return $true
    }
    catch {
        # 检查Docker Compose插件
        try {
            docker compose version 2>$null
            return $true
        }
        catch {
            return $false
        }
    }
}

function Test-DockerService {
    try {
        docker version 2>$null | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# 主部署函数
function Deploy-Application {
    Write-Host "1. 检查Docker安装..." -ForegroundColor Green
    if (-not (Test-Docker)) {
        Write-Host "[错误] 未找到Docker。请先安装Docker Desktop。" -ForegroundColor Red
        Write-Host "下载地址: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        Read-Host "按Enter键退出"
        exit 1
    }
    
    Write-Host "2. 检查Docker Compose..." -ForegroundColor Green
    if (-not (Test-DockerCompose)) {
        Write-Host "[警告] Docker Compose可能未安装，尝试使用Docker Desktop内置版本..." -ForegroundColor Yellow
    }
    
    Write-Host "3. 检查Docker服务状态..." -ForegroundColor Green
    if (-not (Test-DockerService)) {
        Write-Host "[错误] Docker服务未运行。请启动Docker Desktop。" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
    
    Write-Host "4. 构建Docker镜像..." -ForegroundColor Green
    Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Yellow
    docker-compose build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 构建失败！" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
    
    Write-Host "5. 启动服务..." -ForegroundColor Green
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 启动失败！" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
    
    Write-Host "6. 检查服务状态..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    docker-compose ps
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "部署完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "访问地址: https://localhost:8443" -ForegroundColor Yellow
    Write-Host "HTTP地址: http://localhost:5000" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "常用命令:" -ForegroundColor Cyan
    Write-Host "   查看日志: docker-compose logs -f" -ForegroundColor White
    Write-Host "   停止服务: docker-compose down" -ForegroundColor White
    Write-Host "   重启服务: docker-compose restart" -ForegroundColor White
    Write-Host "   进入容器: docker-compose exec jm-tag-to-pdf bash" -ForegroundColor White
    Write-Host ""
    Write-Host "注意: 由于使用自签名证书，浏览器可能会显示安全警告。" -ForegroundColor Yellow
    Write-Host "      可以点击'高级'->'继续前往'来访问。" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# 管理函数
function Show-Menu {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "JM-tag.zip_to_PDF Docker 管理菜单" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 部署应用程序" -ForegroundColor Green
    Write-Host "2. 查看服务状态" -ForegroundColor Green
    Write-Host "3. 查看实时日志" -ForegroundColor Green
    Write-Host "4. 停止服务" -ForegroundColor Green
    Write-Host "5. 重启服务" -ForegroundColor Green
    Write-Host "6. 清理临时文件" -ForegroundColor Green
    Write-Host "7. 更新应用程序" -ForegroundColor Green
    Write-Host "8. 备份数据" -ForegroundColor Green
    Write-Host "9. 退出" -ForegroundColor Red
    Write-Host ""
}

function Manage-Services {
    param(
        [string]$Choice
    )
    
    switch ($Choice) {
        "1" {
            Deploy-Application
            Read-Host "按Enter键返回菜单"
        }
        "2" {
            Write-Host "服务状态:" -ForegroundColor Green
            docker-compose ps
            Read-Host "按Enter键返回菜单"
        }
        "3" {
            Write-Host "查看实时日志 (按Ctrl+C退出)..." -ForegroundColor Green
            docker-compose logs -f
            Read-Host "按Enter键返回菜单"
        }
        "4" {
            Write-Host "停止服务..." -ForegroundColor Yellow
            docker-compose down
            Write-Host "服务已停止" -ForegroundColor Green
            Read-Host "按Enter键返回菜单"
        }
        "5" {
            Write-Host "重启服务..." -ForegroundColor Yellow
            docker-compose restart
            Write-Host "服务已重启" -ForegroundColor Green
            Read-Host "按Enter键返回菜单"
        }
        "6" {
            Write-Host "清理临时文件..." -ForegroundColor Yellow
            docker-compose exec jm-tag-to-pdf python cleanup.py
            Write-Host "临时文件已清理" -ForegroundColor Green
            Read-Host "按Enter键返回菜单"
        }
        "7" {
            Write-Host "更新应用程序..." -ForegroundColor Yellow
            Write-Host "1. 拉取最新代码" -ForegroundColor White
            Write-Host "2. 重建镜像" -ForegroundColor White
            Write-Host "3. 重启服务" -ForegroundColor White
            
            docker-compose down
            docker-compose build --no-cache
            docker-compose up -d
            
            Write-Host "应用程序已更新" -ForegroundColor Green
            Read-Host "按Enter键返回菜单"
        }
        "8" {
            Write-Host "备份数据..." -ForegroundColor Yellow
            $backupFile = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
            Compress-Archive -Path uploads, download, outputs, logs, temp -DestinationPath $backupFile -Force
            Write-Host "数据已备份到: $backupFile" -ForegroundColor Green
            Read-Host "按Enter键返回菜单"
        }
        "9" {
            Write-Host "退出..." -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "无效的选择" -ForegroundColor Red
            Read-Host "按Enter键返回菜单"
        }
    }
}

# 主程序
if ($args.Count -gt 0) {
    # 命令行模式
    switch ($args[0]) {
        "deploy" {
            Deploy-Application
        }
        "start" {
            docker-compose up -d
            Write-Host "服务已启动" -ForegroundColor Green
        }
        "stop" {
            docker-compose down
            Write-Host "服务已停止" -ForegroundColor Green
        }
        "restart" {
            docker-compose restart
            Write-Host "服务已重启" -ForegroundColor Green
        }
        "logs" {
            docker-compose logs -f
        }
        "status" {
            docker-compose ps
        }
        "help" {
            Write-Host "用法: .\deploy.ps1 [命令]" -ForegroundColor Cyan
            Write-Host "命令:" -ForegroundColor Yellow
            Write-Host "  deploy    - 部署应用程序" -ForegroundColor White
            Write-Host "  start     - 启动服务" -ForegroundColor White
            Write-Host "  stop      - 停止服务" -ForegroundColor White
            Write-Host "  restart   - 重启服务" -ForegroundColor White
            Write-Host "  logs      - 查看日志" -ForegroundColor White
            Write-Host "  status    - 查看状态" -ForegroundColor White
            Write-Host "  menu      - 显示管理菜单" -ForegroundColor White
            Write-Host "  help      - 显示帮助" -ForegroundColor White
        }
        "menu" {
            # 进入菜单模式
        }
        default {
            Write-Host "未知命令: $($args[0])" -ForegroundColor Red
            Write-Host "使用 '.\deploy.ps1 help' 查看帮助" -ForegroundColor Yellow
        }
    }
    
    if ($args[0] -ne "menu") {
        exit 0
    }
}

# 交互式菜单模式
while ($true) {
    Show-Menu
    $choice = Read-Host "请选择 (1-9)"
    Manage-Services -Choice $choice
}