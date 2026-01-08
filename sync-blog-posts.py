#!/usr/bin/env python3
"""
Sync blog posts from atsentia-website to GitHub profile README.

Usage:
    python sync-blog-posts.py                    # Preview changes
    python sync-blog-posts.py --write            # Write changes to README
    python sync-blog-posts.py --website-path /path/to/atsentia-website
"""

import os
import re
import argparse
from pathlib import Path
from datetime import datetime

# Default paths (relative to this script's location)
SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_WEBSITE_PATH = SCRIPT_DIR.parent / "atsentia-website"
README_PATH = SCRIPT_DIR / "README.md"
BLOG_CONTENT_DIR = "atsentia/src/content/blog"

# Markers in README
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown file."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            frontmatter[key] = value
    return frontmatter

def get_blog_posts(website_path: Path) -> list[dict]:
    """Read all blog posts and extract metadata."""
    blog_dir = website_path / BLOG_CONTENT_DIR
    posts = []

    if not blog_dir.exists():
        print(f"Error: Blog directory not found: {blog_dir}")
        return posts

    for file_path in blog_dir.glob("*.md"):
        content = file_path.read_text()
        frontmatter = parse_frontmatter(content)

        if not frontmatter.get('title') or not frontmatter.get('pubDate'):
            print(f"Warning: Skipping {file_path.name} - missing title or pubDate")
            continue

        # Parse date
        pub_date = datetime.strptime(frontmatter['pubDate'], '%Y-%m-%d')

        # Generate slug from filename
        slug = file_path.stem

        posts.append({
            'title': frontmatter['title'],
            'slug': slug,
            'date': pub_date,
            'url': f"https://atsentia.ai/blog/{slug}/",
        })

    # Sort by date, newest first
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def format_date(date: datetime) -> str:
    """Format date as 'Mon D, YYYY' (e.g., 'Jan 8, 2026')."""
    return date.strftime('%b %-d, %Y')

def generate_post_list(posts: list[dict]) -> str:
    """Generate markdown list of blog posts."""
    lines = []
    for post in posts:
        date_str = format_date(post['date'])
        lines.append(f"- [{post['title']}]({post['url']}) — {date_str}")
    return '\n'.join(lines)

def update_readme(readme_path: Path, post_list: str, dry_run: bool = True) -> bool:
    """Update README with blog post list between markers."""
    content = readme_path.read_text()

    # Find markers
    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        print(f"Error: Could not find markers in {readme_path}")
        print(f"  Expected: {START_MARKER}")
        print(f"  And: {END_MARKER}")
        return False

    # Build new content
    new_content = (
        content[:start_idx + len(START_MARKER)] +
        '\n' + post_list + '\n' +
        content[end_idx:]
    )

    if dry_run:
        print("=== Preview of changes ===")
        print(f"Would update {readme_path}")
        print()
        print("New blog post section:")
        print(START_MARKER)
        print(post_list)
        print(END_MARKER)
        return True

    readme_path.write_text(new_content)
    print(f"Updated {readme_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Sync blog posts to GitHub README')
    parser.add_argument('--write', action='store_true', help='Write changes (default: dry run)')
    parser.add_argument('--website-path', type=Path, default=DEFAULT_WEBSITE_PATH,
                        help=f'Path to atsentia-website repo (default: {DEFAULT_WEBSITE_PATH})')
    args = parser.parse_args()

    print(f"Reading blog posts from: {args.website_path / BLOG_CONTENT_DIR}")
    posts = get_blog_posts(args.website_path)

    if not posts:
        print("No blog posts found!")
        return 1

    print(f"Found {len(posts)} blog posts:")
    for post in posts:
        print(f"  - {post['title']} ({format_date(post['date'])})")
    print()

    post_list = generate_post_list(posts)

    if not update_readme(README_PATH, post_list, dry_run=not args.write):
        return 1

    if not args.write:
        print()
        print("Run with --write to apply changes")

    return 0

if __name__ == '__main__':
    exit(main())
