import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from markdownify import markdownify


def html_to_markdown(html, crate_name):
    markdown = markdownify(html, heading_style='ATX')

    # Process markdown to remove redundant headers
    crate_normalized = crate_name.replace("-", "_").replace("_", "\\_")
    lines = markdown.split("\n")

    # Find first relevant header (## [crate_name...)
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if line.startswith(f"## [{crate_normalized}"):
            start_idx = i
            break
        
    for i, line in enumerate(lines):
        if line.startswith("## Auto Trait Implementations"):
            end_idx = i
            break

    lines = lines[start_idx or 0:end_idx or -1]
    lines = (line.replace("Copy item path", "") for line in lines)

    return "\n".join(lines)


def crawl_crate_docs(crate, output_dir):
    crate_dir = crate.replace("-", "_")
    base_url = f"https://docs.rs/{crate}/latest/{crate_dir}/"
    start_url = urljoin(base_url, "index.html")

    visited = set()
    queue = [start_url]

    while queue:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        try:
            markdown = html_to_markdown(response.text, crate)
        except RuntimeError as e:
            print(f"Error converting {url}: {e}")
            continue

        parsed_url = urlparse(url)
        path_relative_to_base = parsed_url.path.split(f"/{crate}/latest/{crate_dir}/")[
            -1
        ]

        if path_relative_to_base.endswith("/index.html"):
            dir_part = path_relative_to_base[: -len("index.html")]
            file_path = os.path.join(output_dir, dir_part, "index.md")
        else:
            file_path = os.path.join(
                output_dir, path_relative_to_base.replace(".html", ".md")
            )

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Saved: {file_path}")

        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(url, href)
            parsed_absolute = urlparse(absolute_url)
            normalized_url = parsed_absolute._replace(fragment="", query="").geturl()
            if normalized_url.startswith(base_url) and normalized_url not in visited:
                queue.append(normalized_url)

        # time.sleep(0.25)


def generate_unified_markdown(output_dir):
    for root, dirs, files in os.walk(output_dir, topdown=False):
        md_files = []
        subdirs = []
        for name in files:
            if name == "unified.md":
                continue
            if name.endswith(".md"):
                md_files.append(name)
        for name in dirs:
            subdirs.append(name)

        ordered_files = []
        if "index.md" in md_files:
            ordered_files.append("index.md")
            md_files.remove("index.md")
        ordered_files += sorted(md_files)

        content = []
        for file in ordered_files:
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content.append(f.read())

        for subdir in sorted(subdirs):
            unified_path = os.path.join(root, subdir, "unified.md")
            if os.path.exists(unified_path):
                with open(unified_path, "r", encoding="utf-8") as f:
                    content.append(f.read())

        unified_path = os.path.join(root, "unified.md")
        with open(unified_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(content))
        print(f"Generated unified.md for {root}")


def main():
    parser = argparse.ArgumentParser(
        description="Bundle Rust crate documentation into Markdown files."
    )
    parser.add_argument("crate", help="Name of the Rust crate")
    args = parser.parse_args()

    output_dir = os.path.join(os.getcwd(), "output", args.crate)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Crawling documentation for {args.crate}...")
    crawl_crate_docs(args.crate, output_dir)

    print("Generating unified Markdown files...")
    generate_unified_markdown(output_dir)

    print("Done.")


if __name__ == "__main__":
    main()
