import argparse
import bs4
import requests
import pyperclip
import re
import pypandoc
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

BASE_V2 = "https://www.wattpad.com/apiv2/"
BASE_V3 = "https://www.wattpad.com/api/v3/"
USER_AGENT = {"User-Agent": "Mozilla/5.0"}
ERROR_MSG = (
    "Please check the URL again for a valid story ID. "
    "Contact the developer if you believe this is a bug."
)


def extract_story_id(url: str) -> Optional[str]:
    match = re.search(r"\d{5,}", url)
    return match.group() if match else None


def http_get(url: str) -> Optional[str]:
    try:
        res = requests.get(url, headers=USER_AGENT)
        res.raise_for_status()
        return res.text
    except Exception as exc:
        print(f"HTTP error: {exc}")
        return None


def sanitize_filename(name: str) -> str:
    return re.sub(r"[/\\:*?\"<>|]", "_", name)


def extract_json_fields(data: Dict[str, Any]) -> Tuple[str, str, List[Dict], str, Dict, str]:
    return (
        data.get("description", ""),
        data.get("tags", []),
        data.get("parts", []),
        data.get("title", "Untitled Story"),
        data.get("user", {}),
        data.get("cover", ""),
    )


def write_html(
    file_path: Path,
    title: str,
    author: Dict[str, Any],
    cover: str,
    tags: List[str],
    description: str,
    chapters: List[Dict[str, Any]],
):
    with file_path.open("w", encoding="utf-8") as f:
        f.write(
            f"""
<html>
<head>
    <meta name='title' content='{title}'>
    <meta name='author' content='{author.get("name", "Unknown")}' >
</head>
<body>
<div style="text-align:center;">
    <img src="{cover}" alt="cover_image">
</div>
<h2 align="center">{title}</h2>
<h4 align="center">By {author.get("name", "Unknown")} —
    <a href="https://www.wattpad.com/user/{author.get('username','')}">{author.get('username','')}</a>
</h4>

<div align="center">Tags: {', '.join(tags)}</div>
<br>
<div align="center">{description}</div>
<hr>
            """
        )

        for i, chapter in enumerate(chapters, start=1):
            print(f"Fetching Chapter {i} — {chapter.get('title','(untitled)')}")

            chapter_url = f"{BASE_V2}storytext?id={chapter['id']}"
            html = http_get(chapter_url)
            if not html:
                f.write(f"<h3>Chapter {i}: Error fetching content.</h3>")
                continue

            soup = bs4.BeautifulSoup(html, "html.parser")
            f.write(
                f"<h3>Chapter {i}: {chapter.get('title','(no title)')}</h3>\n" + soup.prettify()
            )

        f.write("</body></html>")

    print(f"Saved HTML → {file_path}")


def convert_to_epub(html_file: Path, title: str, cover_url: str):
    print("Generating EPUB...")
    safe_title = sanitize_filename(title)
    cover_file = Path(f"{safe_title}.jpg")

    try:
        img_res = requests.get(cover_url, headers=USER_AGENT)
        img_res.raise_for_status()
        cover_file.write_bytes(img_res.content)
    except Exception as exc:
        print(f"Cover download failed: {exc}")

    output_epub = Path(f"{safe_title}.epub")

    pypandoc.convert_file(
        str(html_file),
        "epub3",
        outputfile=str(output_epub),
        extra_args=[
            "--epub-chapter-level=2",
            f"--epub-cover-image={cover_file}",
        ],
        sandbox=False,
    )

    if cover_file.exists():
        cover_file.unlink()

    print(f"Saved EPUB → {output_epub}")


def process(url: str):
    story_id = extract_story_id(url)
    if not story_id:
        print(ERROR_MSG)
        return

    story_url = (
        f"{BASE_V3}stories/{story_id}?drafts=0&mature=1&include_deleted=1&"
        "fields=id,title,description,url,cover,user(name,username),parts(id,title),tags"
    )

    try:
        story_json = requests.get(story_url, headers=USER_AGENT).json()
    except Exception as exc:
        print(f"Failed to get JSON: {exc}")
        return

    if story_json.get("result") == "ERROR" or story_json.get("error_type"):
        print(f"API Error: {story_json.get('message','Unknown error')}")
        print(ERROR_MSG)
        return

    description, tags, chapters, title, author, cover = extract_json_fields(story_json)

    safe_title = sanitize_filename(title)
    html_path = Path(f"{safe_title}.html")

    write_html(html_path, title, author, cover, tags, description, chapters)
    convert_to_epub(html_path, title, cover)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Wattpad stories to EPUB.")
    parser.add_argument("url", nargs="?", help="Wattpad story URL")
    args = parser.parse_args()

    process(args.url or pyperclip.paste())
