#!/usr/bin/env python3

# Copyright © 2025 Hugo Dünger -  ZKM | Zentrum für Kunst und Medien Karlsruhe
# Lizenziert unter der MIT-Lizenz

import os
import sys
import shutil
import subprocess
import pathlib
import random
import string
import warnings

# Suppress any library warnings (e.g., DeprecationWarning)
warnings.filterwarnings("ignore")

# --- Configuration ---
HUGO_DIR = pathlib.Path("hugo-page")
NEW_DIR = pathlib.Path("new-content")
DOWNLOAD_DIR = HUGO_DIR / "static" / "downloads"
CONTENT_DIR = HUGO_DIR / "content"
IMAGE_DIR = HUGO_DIR / "static" / "images"
# --- End Configuration ---


# --- Virtual environment bootstrap ---
def ensure_venv():
    venv_path = pathlib.Path(__file__).parent / ".venv"
    if sys.prefix != sys.base_prefix:
        return
    if not venv_path.exists():
        print("Setting up virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
    python_bin = venv_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.check_call([str(python_bin), __file__])
    sys.exit(0)

ensure_venv()
# -------------------------------------


def ensure_package(pkg, import_name=None):
    import importlib
    name = import_name or pkg
    try:
        importlib.import_module(name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])


print("Checking Python dependencies...")
for pkg, imp in [("Pillow", "PIL"), ("PyMuPDF", "fitz"), ("opencv-python", "cv2")]:
    ensure_package(pkg, imp)

from PIL import Image, ImageDraw
import fitz  # PyMuPDF
import cv2


def generate_thumbnail(source_path: pathlib.Path, thumbnail_path: pathlib.Path):
    ext = source_path.suffix.lower()
    try:
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            with Image.open(source_path) as img:
                img.thumbnail((400, 400))
                img.save(thumbnail_path, "PNG")
            return True

        if ext == '.pdf':
            doc = fitz.open(source_path)
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.thumbnail((400, 400))
            img.save(thumbnail_path, "PNG")
            return True

        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            vid = cv2.VideoCapture(str(source_path))
            vid.set(cv2.CAP_PROP_POS_MSEC, 2000)
            success, frame = vid.read()
            vid.release()
            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((400, 400))
                img.save(thumbnail_path, "PNG")
                return True
        return False
    except Exception:
        return False


def create_placeholder(thumbnail_path):
    img = Image.new("RGB", (300, 200), color="grey")
    draw = ImageDraw.Draw(img)
    draw.text((150, 100), "No Preview", fill="white", anchor="mm")
    img.save(thumbnail_path)


def execute_cmd(cmd, cwd=None):
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError:
        return False


def write_resource_file(path: pathlib.Path, filename: str):
    title = filename.replace("-", " ").rsplit(".", 1)[0]
    content = f"---\ntitle: \"{title}\"\ndraft: true\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    print("Checking for required external tools...")
    if shutil.which("hugo") is None:
        print("Error: Hugo not found in PATH.")
        sys.exit(1)
    print("All external dependencies present.\n")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    (CONTENT_DIR / "de" / "resources").mkdir(parents=True, exist_ok=True)
    (CONTENT_DIR / "en" / "resources").mkdir(parents=True, exist_ok=True)

    print(f"Processing files in '{NEW_DIR}/'...\n")

    for source_file_path in NEW_DIR.iterdir():
        if not source_file_path.is_file() or source_file_path.name == ".gitignore":
            continue

        filename = source_file_path.name
        current_source_path = source_file_path

        if (DOWNLOAD_DIR / filename).exists():
            random_str = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
            name_no_ext, ext = os.path.splitext(filename)
            new_filename = f"{name_no_ext}_{random_str}{ext}"
            current_source_path = NEW_DIR / new_filename
            shutil.move(source_file_path, current_source_path)
            filename = new_filename

        name_no_ext = filename.rsplit('.', 1)[0]
        print(f"Processing '{filename}'...")

        rel_de = f"content/de/resources/{name_no_ext}.md"
        rel_en = f"content/en/resources/{name_no_ext}.md"
        de_content_path = HUGO_DIR / rel_de
        en_content_path = HUGO_DIR / rel_en

        # Try to generate with Hugo
        if not execute_cmd(['hugo', 'new', '--kind', 'resource', rel_de], cwd=HUGO_DIR) or not de_content_path.exists():
            write_resource_file(de_content_path, filename)

        if not execute_cmd(['hugo', 'new', '--kind', 'resource', rel_en], cwd=HUGO_DIR) or not en_content_path.exists():
            write_resource_file(en_content_path, filename)

        # Update placeholders
        for content_path in (de_content_path, en_content_path):
            try:
                content = content_path.read_text(encoding='utf-8')
                content = content.replace("/downloads/placeholder.pdf", f"/downloads/{filename}")
                content = content.replace("/images/placeholder.png", f"/images/{name_no_ext}.png")
                content_path.write_text(content, encoding='utf-8')
            except Exception:
                print(f"Could not modify {content_path}")

        # Thumbnail or placeholder
        thumbnail_path = IMAGE_DIR / f"{name_no_ext}.png"
        if not generate_thumbnail(current_source_path, thumbnail_path):
            create_placeholder(thumbnail_path)

        shutil.move(current_source_path, DOWNLOAD_DIR / filename)
        print(f"Done: {filename}\n")

    print("All done.")


if __name__ == "__main__":
    main()
    input("Press Enter to exit...")
