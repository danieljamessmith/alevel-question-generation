#!/usr/bin/env python3
"""
Script to clear output files while maintaining their existence.
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


def main():
    """Main function to clear output files with user confirmation."""
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
    while True:
        response = input("Do you want to clear these files? (Y/N): ").strip().upper()
        if response in ['Y', 'N']:
            break
        print("Please enter Y or N.")
    
    if response == 'N':
        print("Operation cancelled. No files were cleared.")
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
    
    print()
    print(f"Successfully cleared {cleared_count} of {len(existing_files)} file(s).")


if __name__ == "__main__":
    main()

