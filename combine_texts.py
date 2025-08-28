#!/usr/bin/env python3
"""
combine_texts.py

Combines all .txt files in a specified folder into a single file in the project root.
Usage:
    python combine_texts.py /path/to/folder
"""
import sys
import os
from pathlib import Path

def combine_text_files(folder_path: str, output_filename: str = "combined_output.txt"):
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory.")
        sys.exit(1)

    mdx_files = sorted(folder.rglob("*.mdx"))
    if not mdx_files:
        print(f"No .mdx files found in {folder_path} or its subfolders.")
        sys.exit(1)

    output_path = Path.cwd() / "combined_output.mdx"
    with open(output_path, "w", encoding="utf-8") as outfile:
        for i, mdx_file in enumerate(mdx_files):
            with open(mdx_file, "r", encoding="utf-8") as infile:
                if i > 0:
                    outfile.write("\n")
                outfile.write(infile.read())
                outfile.write("\n")
    print(f"Combined {len(mdx_files)} files into {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python combine_texts.py /path/to/folder")
        sys.exit(1)
    combine_text_files(sys.argv[1])
