"""Generate static blog pages from GitHub Issues.

This script expects the following environment variables:
- GITHUB_TOKEN: GitHub token with repo and issues read permissions.
- GITHUB_REPOSITORY: Owner/repo identifier, provided automatically in Actions.
- BLOG_LABEL: Optional label used to filter Issues (default: "blog-post").
- BLOG_OWNER: Optional GitHub login allowed to publish posts (defaults to repository owner).

It renders:
- Individual HTML files per Issue inside the `_posts` directory.
- The list page `list.html` with summaries and links to posts.
- The homepage `index.html` using author data from `config/author.json`.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping

from urllib import parse, request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from markdown import markdown as render_markdown  # noqa: E402
CONFIG_PATH = ROOT / "config" / "author.json"
POST_DIR = ROOT / "_posts"
INDEX_FILE = ROOT / "index.html"
LIST_FILE = ROOT / "list.html"


def load_author_config() -> Mapping[str, str]:
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
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", title).strip("-").lower()
    return slug or "post"


def repository_url() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "your-name/blog-repo")
    return f"https://github.com/{repo}"


def summarize_body(body: str, length: int = 140) -> str:
    condensed = re.sub(r"\s+", " ", body).strip()
    if len(condensed) <= length:
        return condensed
    return condensed[: length - 1].rstrip() + "…"


def fetch_issues(
    token: str, repository: str, allowed_author: str, label: str | None = None
) -> List[MutableMapping[str, str]]:
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
        with request.urlopen(req) as resp:
            payload = resp.read()
            link_header = resp.headers.get("Link", "")

        page_items = [item for item in json.loads(payload) if "pull_request" not in item]
        for issue in page_items:
            if issue["user"]["login"] != allowed_author:
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
    title = issue["title"]
    created_at = dt.datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
    body_html = render_markdown(issue.get("body", ""))
    slug = slugify(title)
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


def write_post_files(issues: Iterable[Mapping[str, str]]) -> List[Mapping[str, str]]:
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
                "summary": summarize_body(issue.get("body", "")),
                "created_at": issue["created_at"],
            }
        )

    return metadata


def render_list(posts: List[Mapping[str, str]]) -> str:
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
    LIST_FILE.write_text(render_list(posts), encoding="utf-8")
    INDEX_FILE.write_text(render_index(author), encoding="utf-8")


def generate() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        raise EnvironmentError("GITHUB_TOKEN and GITHUB_REPOSITORY are required")

    label = os.environ.get("BLOG_LABEL") or None
    repo_owner = repository.split("/", maxsplit=1)[0]
    allowed_author = os.environ.get("BLOG_OWNER", repo_owner)

    issues = fetch_issues(token, repository, allowed_author=allowed_author, label=label)
    post_metadata = write_post_files(issues)
    author = load_author_config()
    write_site_files(post_metadata, author)


if __name__ == "__main__":
    generate()
