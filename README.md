# 轻松博客（Easy-blogging）

轻松博客是一个借助 **GitHub Pages + GitHub Actions + Issue** 的自动化静态博客方案：写好 Issue、打上标签，工作流就会把内容转成统一风格的 HTML 页面并推送到仓库。

## 仓库结构

```
/blog-repo
├── /_posts                # 生成的文章 HTML（由工作流写入）
├── /assets                # 静态资源占位目录
├── /config/author.json    # 作者头像、昵称、介绍等配置
├── /scripts/generate_blog.py
├── /markdown.py           # 轻量 Markdown 转换器（无外部依赖）
├── /index.html            # 主页（作者介绍 + 跳转列表）
├── /list.html             # 文章列表页
├── /style.css             # 统一样式（Vercel 风格）
└── .github/workflows/
    └── blog-post-generator.yml  # Issue 自动生成页面的工作流
```

> `_posts/.gitkeep` 仅用于保持目录存在，实际文章由工作流生成。

## 使用方式

1. **自定义作者信息**：编辑 `config/author.json`，填入头像链接、昵称、签名等，主页会自动读取。
2. **发布文章**：创建 Issue，标题即文章标题，正文写内容（支持基础 Markdown、代码块、列表、链接等）；若设置了 `BLOG_LABEL`，为 Issue 打上该标签即可被收录。
   - `BLOG_LABEL`：标记文章的标签（默认 `blog-post`）。
3. **自定义作者信息**：编辑 `config/author.json`，填入头像链接、昵称、签名等，主页会自动读取。
4. **发布文章**：创建带有 `BLOG_LABEL` 的 Issue，标题即文章标题，正文写内容（支持基础 Markdown、代码块、列表、链接等）。
5. **等待工作流**：工作流会校验 Issue 作者，生成/更新 `_posts/*.html`、`list.html`、`index.html` 并推送回仓库，GitHub Pages 可直接托管这些静态文件。


## 页面样式

- 所有页面共用 `style.css`，风格参考 Vercel 官网：深色背景、玻璃拟态卡片、渐变主色按钮。
- 生成的文章页会自动包含返回首页、文章日期、正文内容等元素。

## 快速开始
直接fork并配置GitHubpages即可！
您无需在意技术细节，如果您碰巧会css，可以自定义样式
当然如果您想要深究技术细节，它也并不复杂：）
