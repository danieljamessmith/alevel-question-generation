#!/usr/bin/env python3
"""
Script to clear output files and img directory while maintaining their existence.
"""

import os
from pathlib import Path

# Define output files to clear
OUTPUT_DIR = Path("output")
OUTPUT_FILES = [
    OUTPUT_DIR / "1_transcribed.jsonl",
    OUTPUT_DIR / "2_perturbed.jsonl",
    OUTPUT_DIR / "3_validated.jsonl",
    OUTPUT_DIR / "4_final_document.tex",
]

# Define img directory
IMG_DIR = Path("img")


def get_confirmation(prompt):
    """Get Y/N confirmation from user."""
    while True:
        response = input(prompt).strip().upper()
        if response in ['Y', 'N']:
            return response == 'Y'
        print("Please enter Y or N.")


def clear_output_files():
    """Clear output files with user confirmation."""
    # Check which files exist
    existing_files = [f for f in OUTPUT_FILES if f.exists()]
    
    if not existing_files:
        print("No output files found to clear.")
        return
    
    # Display files that will be cleared
    print("The following output files will be cleared:")
    for file in existing_files:
        file_size = file.stat().st_size
        print(f"  - {file} ({file_size} bytes)")
    
    print()
    
    # Get user confirmation
    if not get_confirmation("Do you want to clear these output files? (Y/N): "):
        print("Output files were not cleared.")
        return
    
    # Clear the files
    cleared_count = 0
    for file in existing_files:
        try:
            # Open file in write mode and immediately close it to empty it
            with open(file, 'w') as f:
                pass  # File is now empty
            cleared_count += 1
            print(f"✓ Cleared: {file}")
        except Exception as e:
            print(f"✗ Error clearing {file}: {e}")
    
    print(f"Successfully cleared {cleared_count} of {len(existing_files)} output file(s).")


def clear_img_directory():
    """Clear img directory with user confirmation."""
    if not IMG_DIR.exists():
        print(f"\nThe {IMG_DIR} directory does not exist.")
        return
    
    # Get all files in img directory
    img_files = [f for f in IMG_DIR.iterdir() if f.is_file()]
    
    if not img_files:
        print(f"\nNo files found in {IMG_DIR} directory.")
        return
    
    # Display files that will be deleted
    print(f"\nThe following files in {IMG_DIR} directory will be deleted:")
    total_size = 0
    for file in img_files:
        file_size = file.stat().st_size
        total_size += file_size
        print(f"  - {file.name} ({file_size} bytes)")
    print(f"Total: {len(img_files)} file(s), {total_size} bytes")
    
    print()
    
    # Get user confirmation
    if not get_confirmation(f"Do you want to delete all files in {IMG_DIR}? (Y/N): "):
        print(f"Files in {IMG_DIR} were not deleted.")
        return
    
    # Delete the files
    deleted_count = 0
    for file in img_files:
        try:
            file.unlink()
            deleted_count += 1
            print(f"✓ Deleted: {file}")
        except Exception as e:
            print(f"✗ Error deleting {file}: {e}")
    
    print(f"Successfully deleted {deleted_count} of {len(img_files)} file(s) from {IMG_DIR}.")


def main():
    """Main function to clear output files and img directory with user confirmation."""
    clear_output_files()
    print()
    clear_img_directory()


if __name__ == "__main__":
    main()

