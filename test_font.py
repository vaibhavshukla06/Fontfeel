#!/usr/bin/env python3
from font_validator import extract_font_properties
import sys

if len(sys.argv) < 2:
    print("Usage: python test_font.py <font_path>")
    sys.exit(1)

font_path = sys.argv[1]
print(f"Analyzing font: {font_path}")

font_info = extract_font_properties(font_path)
if font_info:
    print(f"Font Format: {font_info.get('format', 'Unknown')}")
    print(f"Font Style: {font_info.get('style', 'Unknown')}")
    print(f"Font Weight: {font_info.get('weight', {}).get('description', 'Unknown')}")
    print(f"Font Width: {font_info.get('width', {}).get('description', 'Unknown')}")
    print(f"Font Shape: {font_info.get('shape', {}).get('type', 'Unknown')}")
    print(f"Font Spacing: {font_info.get('spacing', {}).get('width_type', 'Unknown')} width, {font_info.get('spacing', {}).get('spacing_type', 'Unknown')} spacing")
else:
    print("Failed to analyze font")
