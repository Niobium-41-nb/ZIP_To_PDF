@echo off
chcp 65001 >nul
title 压缩包转PDF工具 - 快速启动

:menu
cls
echo.
echo ========================================
echo         压缩包转PDF工具 v1.0
echo ========================================
echo.
echo 请选择启动模式：
echo.
echo [1] Web界面模式（推荐新手）
echo [2] 命令行下载JM漫画
echo [3] 交互模式
echo [4] 清理临时文件
echo [5] 清理下载文件
echo [6] 查看使用说明
echo [7] 退出
echo.
set /p choice=请输入选择 (1-7): 

if "%choice%"=="1" goto web_mode
if "%choice%"=="2" goto jm_mode
if "%choice%"=="3" goto interactive
if "%choice%"=="4" goto cleanup_temp
if "%choice%"=="5" goto cleanup_download
if "%choice%"=="6" goto show_help
if "%choice%"=="7" goto exit
echo 无效选择，请重新输入
pause
goto menu

:web_mode
echo.
echo 正在启动Web界面...
echo 启动完成后请访问: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
ZipToPDF.exe --web
pause
goto menu

:jm_mode
echo.
set /p jm_id=请输入JM漫画ID:
if "%jm_id%"=="" (
    echo 未输入ID，返回菜单
    pause
    goto menu
)
echo 开始下载JM漫画 %jm_id% ...
ZipToPDF.exe %jm_id%
pause
goto menu

:interactive
echo.
echo 启动交互模式...
ZipToPDF.exe
pause
goto menu

:cleanup_temp
echo.
echo 清理临时文件中...
ZipToPDF.exe --cleanup-temp
pause
goto menu

:cleanup_download
echo.
echo 清理下载文件中...
ZipToPDF.exe --cleanup
pause
goto menu

:show_help
echo.
echo 正在打开使用说明文档...
start "" "可执行文件使用说明.md"
pause
goto menu

:exit
echo.
echo 感谢使用压缩包转PDF工具！
echo.
pause
exit