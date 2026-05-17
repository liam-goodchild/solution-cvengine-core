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
draft: true
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

`slug`, `readTime`, and `draft` are optional. If omitted, the filename and estimated read time are used. Set `draft: true` to keep a post out of the generated site and notification manifest.

## Build locally

From the repository root:

```powershell
python scripts/build_blog.py
```

The build script validates required metadata, skips drafts, deletes generated
HTML for draft posts, writes `frontend/posts/<slug>.html`, updates the Blog list
on `frontend/index.html`, and writes `frontend/blog-manifest.json` for CI
notifications.

## Email notifications

Blog email notifications use Brevo's free tier. Subscriber emails are stored in
Brevo, not Cosmos DB.

Required Azure Static Web App app settings:

- `BREVO_API_KEY`
- `BREVO_LIST_ID`
- `BLOG_NOTIFY_SECRET`
- `EMAIL_FROM`
- `EMAIL_FROM_NAME`
- `EMAIL_DAILY_LIMIT` (default: `250`, capped in code at `250`)
- `PUBLIC_SITE_URL`
- `EMAIL_REPLY_TO` (optional)

Required GitHub environment secrets:

- `BREVO_API_KEY`
- `BLOG_NOTIFY_SECRET`

Required GitHub environment variables:

- `BREVO_LIST_ID`
- `EMAIL_FROM`
- `EMAIL_FROM_NAME`
- `PUBLIC_SITE_URL`
- `EMAIL_DAILY_LIMIT`
- `BLOG_NOTIFY_ON_PUSH` (`false` until tested; set `true` to notify changed posts on branch pushes)

Use a verified Brevo sender on the site domain and add the Brevo-provided SPF,
DKIM, and DMARC records in Cloudflare before sending real notifications.
