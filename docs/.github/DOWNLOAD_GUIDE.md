```markdown
# GitHub Action 使用指南

## 使用方法

1. 进入项目的 **Actions** 页面
2. 选择 **"Download JM Comic and Convert to PDF"** workflow
3. 点击 **"Run workflow"** 按钮
4. 输入参数：
   - **JM漫画ID**: 要下载的漫画ID（例如：422866）
   - **清理临时文件**: 是否在处理完成后清理临时文件（推荐开启）

## 参数说明

- **JM漫画ID**: 禁漫天堂漫画的ID，可以在漫画页面URL中找到
- **清理临时文件**: 处理完成后自动清理临时文件，节省存储空间

## 输出文件

处理完成后，可以在 Artifacts 中下载以下文件：
- 单个PDF文件（按章节分割）
- 完整的ZIP包（包含所有PDF）

## 注意事项

- 每个workflow运行时间限制为6小时
- Artifacts 文件保留7天
- 请遵守相关法律法规，合理使用
```