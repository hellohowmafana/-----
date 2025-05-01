import argparse
import subprocess
import os
import shutil
import zipfile
import cssutils
import re
import json
import xml.etree.ElementTree as ET
import shlex

# Configuration file path
config_file = "config.json"

# Load configuration
def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "ebook_convert": r"Calibre\ebook-convert.exe",
    }

# Load configuration
config = load_config()

# Parse arguments
parser = argparse.ArgumentParser(description="Process MOBI files or folders.")
parser.add_argument("--ebook_convert", default=config["ebook_convert"], help="Path to ebook-convert")
parser.add_argument("mobis_path", nargs="*", help="Paths to MOBI files or folders")
args = parser.parse_args()

# Resolve relative paths to absolute paths
def resolve_path(path):
    return os.path.abspath(path) if not os.path.isabs(path) else path

# Define variables
ebook_convert = resolve_path(args.ebook_convert)
mobis_paths = [resolve_path(path) for path in args.mobis_path]
unpack_folder = resolve_path("unpack")

# Process multiple files and folders
mobi_files = []
for path in mobis_paths:
    path = path.strip('"')  # Remove quotes if present
    if os.path.isfile(path):
        mobi_files.append(path)
    elif os.path.isdir(path):
        mobi_files.extend([os.path.join(path, f) for f in os.listdir(path) if f.endswith(".mobi")])
    else:
        print(f"Warning: Path '{path}' does not exist or is not valid. Skipping...")

for mobi_file in mobi_files:
    if not os.path.exists(mobi_file):
        print(f"Warning: File '{mobi_file}' does not exist. Skipping...")
        continue

    epub_file = "temp" + ".epub"

    # Run the process
    subprocess.run([ebook_convert, mobi_file, epub_file])

    # Delete the unpack folder if it exists
    if os.path.exists(unpack_folder):
        shutil.rmtree(unpack_folder)

    # Unzip the epub_file into the unpack folder
    with zipfile.ZipFile(epub_file, 'r') as zip_ref:
        zip_ref.extractall(unpack_folder)

    # Modify the .calibre CSS rule in unpack/stylesheet.css using cssutils
    stylesheet_path = os.path.join(unpack_folder, "stylesheet.css")
    if os.path.exists(stylesheet_path):
        cssutils.log.setLevel("ERROR")  # Suppress cssutils warnings
        with open(stylesheet_path, 'r+', encoding='utf-8') as css_file:
            css_content = css_file.read()
            stylesheet = cssutils.parseString(css_content)

            # Find or create the body rule
            body_rule = None
            for rule in stylesheet.cssRules:
                if rule.type == rule.STYLE_RULE and rule.selectorText == "body":
                    body_rule = rule
                    break
            if not body_rule:
                body_rule = cssutils.css.CSSStyleRule("body")
                stylesheet.insertRule(body_rule)

            # Update or add declarations for body
            body_rule.style.setProperty("-webkit-writing-mode", "vertical-rl")
            body_rule.style.setProperty("writing-mode", "vertical-rl")
            body_rule.style.setProperty("margin", "5%")
            body_rule.style.setProperty("text-align", "justify")

            # Write back the modified CSS
            css_file.seek(0)
            css_file.write(stylesheet.cssText.decode("utf-8"))
            css_file.truncate()

    # Modify the metadata section in unpack/content.opf
    content_opf_path = os.path.join(unpack_folder, "content.opf")
    if os.path.exists(content_opf_path):
        with open(content_opf_path, 'r+', encoding='utf-8') as opf_file:
            opf_content = opf_file.read()

            # Add or update <meta name="primary-writing-mode">
            if '<meta name="primary-writing-mode"' not in opf_content:
                opf_content = re.sub(
                    r'(</metadata>)',
                    r'    <meta name="primary-writing-mode" content="vertical-rl" />\n\1',
                    opf_content,
                    flags=re.DOTALL
                )

            # Add or update <dc:language>
            if '<dc:language>' in opf_content:
                opf_content = re.sub(
                    r'<dc:language>.*?</dc:language>',
                    '<dc:language>zh-tw</dc:language>',
                    opf_content
                )
            else:
                opf_content = re.sub(
                    r'(<metadata.*?>)',
                    r'\1\n    <dc:language>zh-tw</dc:language>',
                    opf_content,
                    flags=re.DOTALL
                )

            # Write changes back to the file
            opf_file.seek(0)
            opf_file.write(opf_content)
            opf_file.truncate()

    # Replace punctuations in unpack\text\*.html
    text_folder = os.path.join(unpack_folder, "text")
    replacements = {
        "“": "﹃",
        "”": "﹄",
        "‘": "﹁",
        "’": "﹂",
        
        "『": "﹃",
        "』": "﹄",
        "「": "﹁",
        "」": "﹂",

        "（": "︵",
        "）": "︶",
        "《": "︽",
        "》": "︾",
        "〈": "︿",
        "〉": "﹀",
        # Add more replacements here as needed
    }
    if os.path.exists(text_folder):
        for root, _, files in os.walk(text_folder):
            for file in files:
                if file.endswith(".html"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r+', encoding='utf-8') as html_file:
                        content = html_file.read()
                        # Apply replacements
                        for old, new in replacements.items():
                            content = content.replace(old, new)
                        # Write back the modified content
                        html_file.seek(0)
                        html_file.write(content)
                        html_file.truncate()

    # Compress the unpack folder back into epub_file
    with zipfile.ZipFile(epub_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, dirs, files in os.walk(unpack_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, unpack_folder)
                zip_ref.write(file_path, arcname)

    # Run the process to convert epub_file to mobiT_file with --mobi-file-type=both
    mobiT_file = os.path.splitext(mobi_file)[0] + "T.mobi"
    subprocess.run([ebook_convert, epub_file, mobiT_file, "--mobi-file-type=both"])

