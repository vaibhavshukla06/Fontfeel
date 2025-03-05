#!/usr/bin/env python3
"""
Download Variable Fonts

This script downloads a selection of variable fonts from Google Fonts for testing
the variable font support in the Font Validator tool.
"""

import os
import requests
import zipfile
import io
import shutil

# Create a directory for variable fonts
VAR_FONTS_DIR = "variable_fonts"
os.makedirs(VAR_FONTS_DIR, exist_ok=True)

# List of variable fonts to download from Google Fonts
VARIABLE_FONTS = [
    {
        "name": "Roboto Flex",
        "url": "https://fonts.google.com/download?family=Roboto%20Flex",
        "filename": "RobotoFlex-VariableFont_GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght.ttf"
    },
    {
        "name": "Inter",
        "url": "https://fonts.google.com/download?family=Inter",
        "filename": "Inter-VariableFont_slnt,wght.ttf"
    },
    {
        "name": "Source Sans 3",
        "url": "https://fonts.google.com/download?family=Source%20Sans%203",
        "filename": "SourceSans3-VariableFont_wght.ttf"
    },
    {
        "name": "Fraunces",
        "url": "https://fonts.google.com/download?family=Fraunces",
        "filename": "Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf"
    },
    {
        "name": "Anybody",
        "url": "https://fonts.google.com/download?family=Anybody",
        "filename": "Anybody-VariableFont_wdth,wght.ttf"
    }
]

def download_and_extract_font(font_info):
    """Download and extract a font from Google Fonts."""
    print(f"Downloading {font_info['name']}...")
    
    try:
        # Download the zip file
        response = requests.get(font_info['url'])
        response.raise_for_status()
        
        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Find the variable font file
            for file in zip_file.namelist():
                if file.endswith(font_info['filename']):
                    # Extract the file
                    with zip_file.open(file) as source_file:
                        target_path = os.path.join(VAR_FONTS_DIR, os.path.basename(file))
                        with open(target_path, "wb") as target_file:
                            shutil.copyfileobj(source_file, target_file)
                    
                    print(f"  Extracted {os.path.basename(file)}")
                    return True
        
        print(f"  Error: Could not find {font_info['filename']} in the downloaded zip file.")
        return False
    
    except Exception as e:
        print(f"  Error downloading {font_info['name']}: {e}")
        return False

def main():
    """Main function to download all fonts."""
    print(f"Downloading variable fonts to {VAR_FONTS_DIR}/")
    
    success_count = 0
    for font in VARIABLE_FONTS:
        if download_and_extract_font(font):
            success_count += 1
    
    print(f"\nDownloaded {success_count} of {len(VARIABLE_FONTS)} variable fonts.")
    
    if success_count > 0:
        print("\nYou can now test the variable font support with:")
        print(f"python font_analyzer_cli.py {VAR_FONTS_DIR}/ --variable-only --report --visualize")

if __name__ == "__main__":
    main() 