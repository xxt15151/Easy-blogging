# 轻松博客 · Easy-blogging

> Issue 写作、Action 构建、Pages 发布，一站式自动化静态博客模板。

[English Version](README_EN.md)

## 项目简介
轻松博客提供“写好 Issue 即生成博客页面”的极简写作体验：通过 GitHub Actions 自动把带标签的 Issue 渲染为统一风格的静态页面，并推送到仓库供 GitHub Pages 托管。无需手动构建或依赖复杂框架，适合想要快速上线个人博客的用户。

## 功能亮点
- **Issue 即文章**：标题=文章标题，正文支持常用 Markdown、代码块、表格与目录。
- **权限与标签守卫**：工作流在生成前校验作者（`BLOG_OWNER`）和标签（`BLOG_LABEL`），确保只有指定 Issue 被收录。
- **全自动发布**：生成 `_posts`、`list.html`、`index.html` 后自动推送，并触发 Pages 部署工作流。
- **统一设计语言**：`style.css` 提供暗色玻璃拟态风格的卡片、按钮与排版，文章页带返回导航、日期与摘要。
- **轻量依赖**：除 `markdown` 外无额外依赖，核心转换脚本可直接运行。

## 仓库结构
```
/blog-repo
├── /_posts                # 生成的文章 HTML（由工作流写入）
├── /assets                # 静态资源占位目录
├── /config/author.json    # 作者头像、昵称、签名、按钮文案
├── /scripts/generate_blog.py
├── /markdown.py           # 轻量 Markdown 转换器（无外部依赖）
├── /index.html            # 主页（作者信息 + 推荐 CTA）
├── /list.html             # 文章列表页
├── /style.css             # 统一样式（Vercel 风格）
└── .github/workflows/
    ├── blog-post-generator.yml  # Issue 自动生成页面
    └── static.yml               # 推送后触发 Pages 部署
```

## 快速开始
1. **Fork 仓库并开启 Pages**：将 Pages 分支设置为 `main`（或默认分支）。
2. **配置变量（可选）**：在仓库 Settings → Variables 中设置：
   - `BLOG_LABEL`：收录文章的标签，默认 `blog-post`。
   - `BLOG_OWNER`：允许创建文章 Issue 的 GitHub 用户名，默认仓库拥有者。
3. **自定义作者信息**：编辑 `config/author.json`，填入头像链接、昵称、签名与按钮文案。
4. **提交一次变更**：推送到 `main`，以便 Pages 完成初次部署。
5. **发布文章**：创建带 `BLOG_LABEL` 的 Issue，标题即文章标题，正文写内容即可。
6. **等待自动构建**：工作流会生成/更新文章文件并推送，随后 Pages 自动上线。

## 工作流说明
- **Blog post generator** (`.github/workflows/blog-post-generator.yml`)
  - 触发：Issue 创建/编辑/打标签/重开/删除，或手动 `workflow_dispatch`。
  - 步骤：
    1. 校验 Issue 作者（可选）并在不符时自动关闭。
    2. 安装依赖，运行 `scripts/generate_blog.py` 从符合条件的 Issue 渲染静态页。
    3. 若存在更新则提交并推送，再触发 Pages 部署工作流。
- **Deploy static content to Pages** (`.github/workflows/static.yml`)
  - 触发：推送至 `main` 分支或手动触发。
  - 作用：上传整个仓库为 Pages Artifact 并部署到 GitHub Pages。

## 自定义与扩展
- **样式**：调整 `style.css` 即可修改配色、字体与卡片效果。
- **主页信息**：`config/author.json` 控制头像、昵称、签名、CTA 按钮文案。
- **静态资源**：在 `/assets` 放置图片等资源，文章可直接引用。
- **本地试用**：`pip install -r requirements.txt` 后运行 `python scripts/generate_blog.py`，需要设置 `GITHUB_TOKEN`、`BLOG_LABEL`、`BLOG_OWNER` 环境变量以从 Issue 拉取数据。

欢迎基于此模板进行二次创作，祝写作愉快！
