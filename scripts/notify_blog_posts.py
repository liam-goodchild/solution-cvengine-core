#!/usr/bin/env python3
"""Trigger blog post email notifications after a Static Web App deployment.

The script reads frontend/blog-manifest.json, selects published posts, and calls
the deployed /api/NotifyPost endpoint. It deliberately has no third-party
dependencies so it can run in GitHub Actions and locally.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "frontend" / "blog-manifest.json"


def run_git(args: list[str]) -> str:
    """Run a git command and return stdout."""

    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def resolve_base_ref(base: str | None, head: str) -> str | None:
    """Resolve a useful base ref for changed-post detection."""

    if base and set(base) != {"0"}:
        return base

    candidates = [
        ["merge-base", head, "origin/main"],
        ["merge-base", head, "main"],
        ["rev-parse", f"{head}~1"],
    ]

    for candidate in candidates:
        try:
            return run_git(candidate)
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    return None


def changed_blog_sources(base: str | None, head: str) -> set[str]:
    """Return Markdown blog source paths changed between two refs."""

    resolved_base = resolve_base_ref(base, head)
    if not resolved_base:
        return set()

    try:
        output = run_git(
            [
                "diff",
                "--name-only",
                "--diff-filter=ACMR",
                resolved_base,
                head,
                "--",
                "docs/blog",
            ]
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()

    return {
        line.strip().replace("\\", "/")
        for line in output.splitlines()
        if line.strip().lower().endswith(".md")
    }


def load_posts(manifest_path: Path) -> list[dict[str, Any]]:
    """Load published posts from the build manifest."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return list(manifest.get("posts", []))


def select_posts(
    posts: list[dict[str, Any]],
    mode: str,
    base: str | None,
    head: str,
) -> list[dict[str, Any]]:
    """Select which posts should be passed to NotifyPost."""

    if mode == "none":
        return []

    if mode == "all":
        return posts

    changed_sources = changed_blog_sources(base, head)
    return [post for post in posts if post.get("sourcePath") in changed_sources]


def notify_post(  # pylint: disable=too-many-arguments
    post: dict[str, Any],
    site_url: str,
    notify_url: str,
    secret: str,
    commit_sha: str,
    timeout: int,
) -> tuple[bool, str]:
    """Call /api/NotifyPost for a single manifest post."""

    post_url = urljoin(site_url.rstrip("/") + "/", str(post["href"]))
    payload = {
        "slug": post["slug"],
        "title": post["title"],
        "description": post["description"],
        "publishedDate": post["date"],
        "url": post_url,
        "commitSha": commit_sha,
    }
    request = Request(
        notify_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-notify-secret": secret,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310
            body = response.read().decode("utf-8")
            return True, body
    except HTTPError as error:
        body = error.read().decode("utf-8")
        return False, f"HTTP {error.code}: {body}"
    except URLError as error:
        return False, str(error)


def append_step_summary(lines: list[str]) -> None:
    """Append notification results to the GitHub Actions step summary."""

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write("\n".join(lines))
        summary.write("\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--mode",
        choices=["none", "changed", "all"],
        default=os.environ.get("BLOG_NOTIFY_MODE", "changed"),
    )
    parser.add_argument("--base", default=os.environ.get("GITHUB_EVENT_BEFORE"))
    parser.add_argument("--head", default=os.environ.get("GITHUB_SHA", "HEAD"))
    parser.add_argument("--site-url", default=os.environ.get("PUBLIC_SITE_URL"))
    parser.add_argument("--notify-url", default=os.environ.get("BLOG_NOTIFY_URL"))
    parser.add_argument("--secret", default=os.environ.get("BLOG_NOTIFY_SECRET"))
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run notification discovery and delivery."""

    args = parse_args()
    posts = load_posts(args.manifest)
    selected_posts = select_posts(posts, args.mode, args.base, args.head)
    lines = ["## Blog notifications", ""]

    if not selected_posts:
        message = f"No published blog posts selected for notification (mode: {args.mode})."
        print(message)
        lines.append(f"- {message}")
        append_step_summary(lines)
        return 0

    if not args.site_url:
        print("PUBLIC_SITE_URL is required when posts are selected.", file=sys.stderr)
        return 1

    notify_url = args.notify_url or urljoin(
        args.site_url.rstrip("/") + "/",
        "api/NotifyPost",
    )

    if not args.secret and not args.dry_run:
        message = "BLOG_NOTIFY_SECRET is not set; skipping notification calls."
        print(message)
        lines.append(f"- {message}")
        append_step_summary(lines)
        return 0

    failures = 0
    for post in selected_posts:
        slug = post["slug"]

        if args.dry_run:
            message = f"DRY RUN: would notify subscribers for {slug}."
            print(message)
            lines.append(f"- {message}")
            continue

        ok, result = notify_post(
            post=post,
            site_url=args.site_url,
            notify_url=notify_url,
            secret=args.secret,
            commit_sha=args.commit_sha,
            timeout=args.timeout,
        )
        status = "sent/skipped" if ok else "failed"
        print(f"{slug}: {status} - {result}")
        lines.append(f"- `{slug}`: {status}")
        if not ok:
            failures += 1

    append_step_summary(lines)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
