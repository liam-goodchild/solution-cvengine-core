# Blog posts

Create one Markdown file per article in this directory. The build script generates:

- `frontend/posts/<slug>.html`
- the Blog list on `frontend/index.html`

## New post template

````markdown
---
title: "My Post Title"
description: "A short one-line summary shown on the generated post page."
date: "2026-04-24"
readTime: "4 min"
tags:
  - Azure
  - DevOps
slug: "my-post-title"
---

## First section

Write the post in Markdown.

- Bullets are supported
- Numbered lists are supported
- Blockquotes are supported

```bash
terraform fmt -check
terraform validate
```
````

`slug` and `readTime` are optional. If omitted, the filename and estimated read time are used.

## Build locally

From the repository root:

```powershell
python scripts/build_blog.py
```
