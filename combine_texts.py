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

    txt_files = sorted(folder.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {folder_path}.")
        sys.exit(1)

    output_path = Path.cwd() / output_filename
    with open(output_path, "w", encoding="utf-8") as outfile:
        for i, txt_file in enumerate(txt_files):
            with open(txt_file, "r", encoding="utf-8") as infile:
                if i > 0:
                    outfile.write("\n---\n")
                outfile.write(infile.read())
                outfile.write("\n")
    print(f"Combined {len(txt_files)} files into {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python combine_texts.py /path/to/folder")
        sys.exit(1)
    combine_text_files(sys.argv[1])
