from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
# 修改点：添加了 Iterable
from typing import List, Mapping, MutableMapping, Iterable

from urllib import parse, request
import markdown  # 需要 pip install markdown

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CONFIG_PATH = ROOT / "config" / "author.json"
POST_DIR = ROOT / "_posts"
INDEX_FILE = ROOT / "index.html"
LIST_FILE = ROOT / "list.html"


def load_author_config() -> Mapping[str, str]:
    """加载作者配置"""
    default = {
        "name": "轻松博客",
        "tagline": "记录灵感，自动上线",
        "bio": "通过 Issue 写博客，GitHub Actions 自动生成静态站点。",
        "avatar": "https://avatars.githubusercontent.com/u/9919?v=4",
        "cta_text": "查看全部文章",
    }
    if not CONFIG_PATH.exists():
        return default

    with CONFIG_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)

    return {**default, **{k: v for k, v in data.items() if isinstance(v, str)}}


def slugify(title: str) -> str:
    """生成文章的 slug"""
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", title).strip("-").lower()
    return slug or "post"


def repository_url() -> str:
    """获取仓库的 URL"""
    repo = os.getenv("GITHUB_REPOSITORY", "your-name/blog-repo")
    return f"https://github.com/{repo}"


def summarize_body(body: str, length: int = 140) -> str:
    """从 Issue 内容中提取摘要"""
    condensed = re.sub(r"\s+", " ", body).strip()
    if len(condensed) <= length:
        return condensed
    return condensed[: length - 1].rstrip() + "…"


def fetch_issues(
    token: str, repository: str, label: str | None = None, allowed_author: str | None = None
) -> List[MutableMapping[str, str]]:
    """Fetch issues from GitHub API"""
    url = f"https://api.github.com/repos/{repository}/issues"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    params = {
        "state": "open",
        "per_page": 100,
        "sort": "created",
        "direction": "desc",
    }
    if label:
        params["labels"] = label

    issues: List[MutableMapping[str, str]] = []

    while url:
        query = f"?{parse.urlencode(params)}" if params else ""
        req = request.Request(url + query, headers=headers)
        
        # 增加简单的错误处理，防止 API 请求失败导致崩溃
        try:
            with request.urlopen(req) as resp:
                payload = resp.read()
                link_header = resp.headers.get("Link", "")
        except Exception as e:
            print(f"Error fetching issues: {e}")
            break

        page_items = [item for item in json.loads(payload) if "pull_request" not in item]
        for issue in page_items:
            # 安全检查：防止 user 字段为空的情况（极少见但可能）
            if issue.get("user") and issue["user"].get("login") != allowed_author:
                continue
            issues.append(issue)

        url = None
        for link in link_header.split(","):
            segments = link.split(";")
            if len(segments) < 2:
                continue
            if 'rel="next"' in segments[1]:
                candidate = segments[0].strip()
                if candidate.startswith("<") and candidate.endswith(">"):
                    url = candidate[1:-1]
                break
        params = None

    return issues


def render_post(issue: Mapping[str, str]) -> str:
    """渲染单篇文章为 HTML"""
    title = issue["title"]
    # 处理日期格式，兼容 Python < 3.11
    created_at_str = issue["created_at"].replace("Z", "+00:00")
    created_at = dt.datetime.fromisoformat(created_at_str)
    
    body_html = markdown.markdown(issue.get("body", "") or "", extensions=["fenced_code", "tables", "toc"])
    
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title} | 轻松博客</title>
  <link rel=\"stylesheet\" href=\"../style.css\" />
</head>
<body>
  <header class=\"top-nav\">
    <a href=\"../index.html\" class=\"brand\">轻松博客</a>
    <a class=\"ghost-btn\" href=\"../list.html\">返回列表</a>
  </header>
  <main class=\"page\">
    <article class=\"card article\">
      <p class=\"eyebrow\">发布于 {created_at.strftime('%Y-%m-%d')}</p>
      <h1>{title}</h1>
      <div class=\"article-body\">{body_html}</div>
    </article>
  </main>
</body>
</html>"""


def remove_stale_posts(valid_slugs: set[str]) -> None:
    """删除已不存在的 Issue 对应的文章文件"""
    if not POST_DIR.exists():
        return

    for post_file in POST_DIR.glob("*.html"):
        if post_file.stem not in valid_slugs:
            post_file.unlink()


def write_post_files(issues: Iterable[Mapping[str, str]]) -> List[Mapping[str, str]]:
    """将每个 Issue 渲染成 HTML 文件并保存"""
    POST_DIR.mkdir(parents=True, exist_ok=True)
    metadata: List[Mapping[str, str]] = []

    for issue in issues:
        title = issue["title"]
        slug = slugify(title)
        html = render_post(issue)
        path = POST_DIR / f"{slug}.html"
        path.write_text(html, encoding="utf-8")
        metadata.append(
            {
                "title": title,
                "slug": slug,
                "summary": summarize_body(issue.get("body", "") or ""),
                "created_at": issue["created_at"],
            }
        )

    return metadata


def render_list(posts: List[Mapping[str, str]]) -> str:
    """渲染文章列表页面"""
    sorted_posts = sorted(posts, key=lambda post: post["created_at"], reverse=True)
    cards = []
    for post in sorted_posts:
        cards.append(
            f"""
        <a class=\"card post-card\" href=\"_posts/{post['slug']}.html\">
          <p class=\"eyebrow\">{post['created_at'][:10]}</p>
          <h2>{post['title']}</h2>
          <p class=\"muted\">{post['summary']}</p>
        </a>"""
        )

    content = "\n".join(cards) or "<p class=\"muted\">还没有文章，快去创建一个带 blog-post 标签的 Issue 吧。</p>"
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>文章列表 | 轻松博客</title>
  <link rel=\"stylesheet\" href=\"style.css\" />
</head>
<body>
  <header class=\"top-nav\">
    <a href=\"index.html\" class=\"brand\">轻松博客</a>
    <a class=\"ghost-btn\" href=\"{repository_url()}/issues\">提交文章 Issue</a>
  </header>
  <main class=\"page\">
    <section class=\"section-heading\">
      <p class=\"eyebrow\">所有文章</p>
      <h1>Issue 驱动的创作</h1>
      <p class=\"muted\">带有 blog-post 标签的 Issue 会自动出现在这里。</p>
    </section>
    <div class=\"grid\">{content}</div>
  </main>
</body>
</html>"""


def render_index(author: Mapping[str, str]) -> str:
    """渲染首页"""
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{author['name']} | 轻松博客</title>
  <link rel=\"stylesheet\" href=\"style.css\" />
</head>
<body>
  <div class=\"hero\">
    <div class=\"glass\">
      <p class=\"eyebrow\">轻松博客 · GitHub Pages</p>
      <h1>{author['name']}</h1>
      <p class=\"lead\">{author['tagline']}</p>
      <p class=\"muted\">{author['bio']}</p>
      <div class=\"actions\">
        <a class=\"primary-btn\" href=\"list.html\">{author['cta_text']}</a>
        <a class=\"ghost-btn\" href=\"{repository_url()}\">仓库</a>
      </div>
    </div>
    <div class=\"avatar\">
      <img alt=\"作者头像\" src=\"{author['avatar']}\" />
    </div>
  </div>
</body>
</html>"""


def write_site_files(posts: List[Mapping[str, str]], author: Mapping[str, str]) -> None:
    """生成并保存所有静态网页文件"""
    LIST_FILE.write_text(render_list(posts), encoding="utf-8")
    INDEX_FILE.write_text(render_index(author), encoding="utf-8")


def generate() -> None:
    """生成静态博客页面"""
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        print("Error: GITHUB_TOKEN and GITHUB_REPOSITORY are required.")
        return

    label = os.environ.get("BLOG_LABEL") or None
    repo_owner = repository.split("/", maxsplit=1)[0]
    
    # --- 修改开始 ---
    # 修复逻辑：如果环境变量获取到的是空字符串，也要使用 repo_owner
    env_author = os.environ.get("BLOG_OWNER")
    allowed_author = env_author if env_author else repo_owner
    # --- 修改结束 ---

    print(f"Fetching issues from {repository} (Author: {allowed_author}, Label: {label})...")
    issues = fetch_issues(token, repository, allowed_author=allowed_author, label=label)
    print(f"Found {len(issues)} issues.")
    
    post_metadata = write_post_files(issues)
    remove_stale_posts({post["slug"] for post in post_metadata})
    author = load_author_config()
    write_site_files(post_metadata, author)
    print("Blog generated successfully.")


if __name__ == "__main__":
    generate()
