@echo off
echo ========================================
echo 压缩包转PDF工具 - 功能测试
echo ========================================
echo.

echo 1. 测试帮助信息...
dist\压缩包转PDF工具.exe --help
echo.

echo 2. 测试Web模式启动（将在后台启动）...
start dist\压缩包转PDF工具.exe --web
echo Web模式已启动，请访问 http://localhost:5000
echo.

echo 3. 测试清理功能...
dist\压缩包转PDF工具.exe --cleanup-temp
echo.

echo 4. 测试交互模式...
echo 请手动运行: dist\压缩包转PDF工具.exe
echo.

pause