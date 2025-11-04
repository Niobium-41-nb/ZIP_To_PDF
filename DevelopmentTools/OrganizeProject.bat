@echo off
chcp 65001 >nul
title 项目整理工具

echo ========================================
echo         项目文件整理工具
echo ========================================
echo.

echo 正在清理临时文件...
if exist __pycache__ rmdir /s /q __pycache__
if exist build rmdir /s /q build
if exist *.spec del /q *.spec

echo.
echo 正在创建干净的源码目录...
mkdir SourceCode
xcopy app.py SourceCode\ /Y
xcopy run.py SourceCode\ /Y
xcopy config.py SourceCode\ /Y
xcopy requirements.txt SourceCode\ /Y
xcopy LICENSE SourceCode\ /Y
xcopy README.md SourceCode\ /Y

xcopy templates SourceCode\templates\ /E /Y
xcopy static SourceCode\static\ /E /Y
xcopy utils SourceCode\utils\ /E /Y
xcopy .github SourceCode\.github\ /E /Y

echo.
echo 正在创建文档目录...
mkdir Documentation
move PackagingPlan.md Documentation\ 2>nul
move ReleaseNotes.md Documentation\ 2>nul
move UserManual.md Documentation\ 2>nul

echo.
echo 正在创建开发工具目录...
mkdir DevelopmentTools
move TestExecutable.bat DevelopmentTools\ 2>nul
move QuickStart.bat DevelopmentTools\ 2>nul
move OrganizeProject.bat DevelopmentTools\ 2>nul

echo.
echo 项目整理完成！
echo.
echo 目录结构：
echo ├── Release/          - Executable distribution package
echo ├── SourceCode/       - Clean source code
echo ├── Documentation/    - Project documentation
echo ├── DevelopmentTools/ - Development and testing tools
echo └── dist/            - Build output directory
echo.
pause