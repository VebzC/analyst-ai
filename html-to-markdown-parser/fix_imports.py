#!/usr/bin/env python3
"""
Script to automatically update import statements from html_to_markdown to html_to_md
throughout the project.
"""
import os
import re
import glob

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace import statements
    updated_content = re.sub(
        r'from\s+html_to_markdown\s+import',
        'from html_to_md import',
        content
    )
    updated_content = re.sub(
        r'from\s+html_to_markdown\.',
        'from html_to_md.',
        updated_content
    )
    updated_content = re.sub(
        r'import\s+html_to_markdown\s+',
        'import html_to_md ',
        updated_content
    )
    
    # If changes were made, write the file
    if content != updated_content:
        print(f"Updating imports in {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)


def main():
    """Find and update all Python files in the project."""
    # Get all .py files
    python_files = glob.glob("**/*.py", recursive=True)
    
    # Process each file
    for file_path in python_files:
        try:
            fix_imports_in_file(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print("Done!")


if __name__ == "__main__":
    main() 