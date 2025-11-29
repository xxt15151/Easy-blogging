# Easy-blogging

> Write with Issues, build with Actions, ship with Pages. A fully automated static blog template.

[查看中文说明](README.md)

## Overview
Easy-blogging turns GitHub Issues into polished static pages. Any Issue with the target label is rendered by a GitHub Actions workflow, committed back to the repository, and served via GitHub Pages. No frameworks or heavy tooling are required, making it ideal for lightweight personal blogs.

## Highlights
- **Issues become posts**: Issue title = post title; body supports Markdown, fenced code blocks, tables, and TOC.
- **Author & label guardrails**: The workflow checks `BLOG_OWNER` and `BLOG_LABEL` before generating pages, so only approved Issues are published.
- **Hands-free publishing**: Generates `_posts`, `list.html`, and `index.html`, commits changes, then triggers the Pages deploy workflow automatically.
- **Consistent design**: `style.css` provides a dark, glassy aesthetic with cards, buttons, and article layout including navigation and dates.
- **Minimal dependencies**: Only the `markdown` package is required; the rest is pure Python and static assets.

## Repository layout
```
/blog-repo
├── /_posts                # Generated post HTML files (written by the workflow)
├── /assets                # Placeholder for static assets
├── /config/author.json    # Avatar, name, bio, CTA text
├── /scripts/generate_blog.py
├── /markdown.py           # Lightweight Markdown converter (no external deps)
├── /index.html            # Home page (author info + CTA)
├── /list.html             # Post list page
├── /style.css             # Shared styles (Vercel-inspired)
└── .github/workflows/
    ├── blog-post-generator.yml  # Issue-to-page pipeline
    └── static.yml               # Pages deployment on push
```

## Quick start
1. **Fork and enable Pages**: Set GitHub Pages to serve from the `main` branch (or your default branch).
2. **Configure variables (optional)** under Repository Settings → Variables:
   - `BLOG_LABEL`: Label to collect posts, default `blog-post`.
   - `BLOG_OWNER`: GitHub username allowed to create post Issues, default is the repo owner.
3. **Customize author info**: Update `config/author.json` with avatar URL, display name, bio, and CTA text.
4. **Make an initial push** to `main` so Pages can complete the first deployment.
5. **Publish a post**: Open an Issue with the `BLOG_LABEL`; the title becomes the post title and the body is the content.
6. **Let automation work**: The workflow renders/updates pages and commits them; GitHub Pages then serves the updated site.

## Workflows
- **Blog post generator** (`.github/workflows/blog-post-generator.yml`)
  - **Triggers**: Issue open/edit/label/reopen/delete, or manual `workflow_dispatch`.
  - **Steps**:
    1. Optionally close Issues not opened by `BLOG_OWNER`.
    2. Install dependencies and run `scripts/generate_blog.py` to render static pages from eligible Issues.
    3. Commit and push changes if any, then dispatch the Pages deploy workflow.
- **Deploy static content to Pages** (`.github/workflows/static.yml`)
  - **Triggers**: Pushes to `main` or manual dispatch.
  - **Purpose**: Uploads the repository as a Pages artifact and deploys it to GitHub Pages.

## Customization
- **Styling**: Edit `style.css` to tweak colors, typography, and card visuals.
- **Home content**: Adjust avatar, name, bio, and CTA text in `config/author.json`.
- **Author config details**: `author.json` ships with `name`, `tagline`, `bio`, `avatar`, and `cta_text`. The generator reloads these values and rewrites `index.html` every time a post build runs, so changing the config alone won't alter the live site until the next post publish (or a manual run of `scripts/generate_blog.py`).
- **Assets**: Place images and media under `/assets` and reference them directly in posts.
- **Local preview**: `pip install -r requirements.txt`, then run `python scripts/generate_blog.py` with `GITHUB_TOKEN`, `BLOG_LABEL`, and `BLOG_OWNER` set to fetch Issues.

Enjoy blogging with a zero-fuss pipeline!
