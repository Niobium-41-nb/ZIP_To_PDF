```markdown
# GitHub Action 下载指南

## 如何下载生成的文件

1. **进入 Actions 页面**
   - 在 GitHub 仓库页面点击 **Actions** 标签
   - 找到 "Download JM Comic and Convert to PDF" workflow
   - 点击最近一次成功的运行

2. **下载 Artifacts**
   - 在运行详情页面找到 **Artifacts** 部分
   - 点击 `jm-<ID>-pdf` 链接下载所有生成的文件
   - 解压下载的ZIP文件获得PDF

3. **文件说明**
   - `.pdf` 文件: 转换后的漫画PDF
   - `.zip` 文件: 包含所有PDF的压缩包

## 注意事项

- Artifacts 文件保留 7 天
- 大文件可能需要一些时间处理
- 如果处理失败，请检查日志中的错误信息
```