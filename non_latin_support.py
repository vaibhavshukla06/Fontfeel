#!/usr/bin/env python3
"""
Non-Latin Script Support Module

This module extends the Font Validator to better support non-Latin scripts,
allowing analysis of fonts with characters from different writing systems.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import unicodedata

# Unicode block ranges for different scripts
SCRIPT_RANGES = {
    'Latin': [
        (0x0020, 0x007F),  # Basic Latin
        (0x00A0, 0x00FF),  # Latin-1 Supplement
        (0x0100, 0x017F),  # Latin Extended-A
        (0x0180, 0x024F)   # Latin Extended-B
    ],
    'Cyrillic': [
        (0x0400, 0x04FF),  # Cyrillic
        (0x0500, 0x052F)   # Cyrillic Supplement
    ],
    'Greek': [
        (0x0370, 0x03FF)   # Greek and Coptic
    ],
    'Arabic': [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F)   # Arabic Supplement
    ],
    'Hebrew': [
        (0x0590, 0x05FF)   # Hebrew
    ],
    'Devanagari': [
        (0x0900, 0x097F)   # Devanagari
    ],
    'Thai': [
        (0x0E00, 0x0E7F)   # Thai
    ],
    'CJK': [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
        (0x3130, 0x318F)   # Hangul Compatibility Jamo
    ],
    'Hangul': [
        (0xAC00, 0xD7AF)   # Hangul Syllables
    ]
}

def detect_supported_scripts(font):
    """
    Detect which scripts are supported by the font.
    
    Args:
        font: A TTFont object.
        
    Returns:
        dict: Dictionary with script names as keys and support level as values.
    """
    supported_scripts = {}
    cmap = font.getBestCmap()
    
    if not cmap:
        return {'error': 'No character map found in font'}
    
    # Check each script
    for script_name, ranges in SCRIPT_RANGES.items():
        char_count = 0
        supported_chars = 0
        
        # Check each range in the script
        for start, end in ranges:
            for char_code in range(start, end + 1):
                # Skip control characters and non-characters
                if unicodedata.category(chr(char_code)).startswith('C'):
                    continue
                
                char_count += 1
                if char_code in cmap:
                    supported_chars += 1
        
        # Calculate support percentage
        if char_count > 0:
            support_level = supported_chars / char_count
            
            # Classify support level
            if support_level > 0.9:
                status = "full"
            elif support_level > 0.5:
                status = "partial"
            elif support_level > 0.1:
                status = "minimal"
            elif support_level > 0:
                status = "limited"
            else:
                status = "none"
            
            supported_scripts[script_name] = {
                'status': status,
                'percentage': support_level * 100,
                'supported_chars': supported_chars,
                'total_chars': char_count
            }
    
    return supported_scripts

def get_script_sample_text(script_name):
    """
    Get sample text for a specific script.
    
    Args:
        script_name: Name of the script.
        
    Returns:
        str: Sample text in the specified script.
    """
    samples = {
        'Latin': 'The quick brown fox jumps over the lazy dog. 0123456789',
        'Cyrillic': 'Быстрая коричневая лиса прыгает через ленивую собаку. 0123456789',
        'Greek': 'Η γρήγορη καφέ αλεπού πηδάει πάνω από το τεμπέλικο σκυλί. 0123456789',
        'Arabic': 'الثعلب البني السريع يقفز فوق الكلب الكسول. ٠١٢٣٤٥٦٧٨٩',
        'Hebrew': 'השועל החום המהיר קופץ מעל הכלב העצלן. 0123456789',
        'Devanagari': 'तेज़ भूरी लोमड़ी आलसी कुत्ते पर कूदती है। ०१२३४५६७८९',
        'Thai': 'สุนัขจิ้งจอกสีน้ำตาลเร็วกระโดดข้ามสุนัขขี้เกียจ 0123456789',
        'CJK': '敏捷的棕色狐狸跳过懒狗。あいうえお。カキクケコ。0123456789',
        'Hangul': '빠른 갈색 여우가 게으른 개를 뛰어 넘습니다. 0123456789'
    }
    
    return samples.get(script_name, "Sample text not available for this script.")

def render_script_samples(font_path, supported_scripts, output_dir=None):
    """
    Render samples of supported scripts.
    
    Args:
        font_path: Path to the font file.
        supported_scripts: Dictionary of supported scripts.
        output_dir: Directory to save visualizations. If None, displays them instead.
        
    Returns:
        dict: Paths to generated sample files if output_dir is provided, otherwise None.
    """
    # Create output directory if needed
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Dictionary to store paths to sample files
    sample_paths = {}
    
    # Get font name for file naming
    font_name = os.path.basename(font_path).split('.')[0]
    
    # Create a figure for all script samples
    fig, axs = plt.subplots(len(supported_scripts), 1, figsize=(12, 2 * len(supported_scripts)))
    
    # If only one script, make axs iterable
    if len(supported_scripts) == 1:
        axs = [axs]
    
    # Render each supported script
    for i, (script_name, info) in enumerate(supported_scripts.items()):
        if info['status'] == 'none':
            continue
        
        sample_text = get_script_sample_text(script_name)
        
        # Create a text rendering
        axs[i].text(0.5, 0.5, f"{script_name} ({info['status']}): {sample_text}", 
                   ha='center', va='center', fontsize=12)
        axs[i].axis('off')
    
    plt.tight_layout()
    
    # Save or display
    if output_dir:
        sample_path = os.path.join(output_dir, f"{font_name}_script_samples.png")
        plt.savefig(sample_path, dpi=300, bbox_inches='tight')
        sample_paths['script_samples'] = sample_path
        plt.close(fig)
    else:
        plt.show()
    
    # Create a visualization of script support levels
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scripts = []
    percentages = []
    colors = []
    
    for script_name, info in supported_scripts.items():
        scripts.append(script_name)
        percentages.append(info['percentage'])
        
        # Set color based on support level
        if info['status'] == 'full':
            colors.append('#2ecc71')  # Green
        elif info['status'] == 'partial':
            colors.append('#f39c12')  # Orange
        elif info['status'] == 'minimal':
            colors.append('#e74c3c')  # Red
        else:
            colors.append('#95a5a6')  # Gray
    
    # Create horizontal bar chart
    y_pos = np.arange(len(scripts))
    ax.barh(y_pos, percentages, align='center', color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(scripts)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel('Support Percentage')
    ax.set_title('Script Support Levels')
    
    # Add percentage labels
    for i, v in enumerate(percentages):
        ax.text(v + 1, i, f"{v:.1f}%", va='center')
    
    plt.tight_layout()
    
    # Save or display
    if output_dir:
        support_path = os.path.join(output_dir, f"{font_name}_script_support.png")
        plt.savefig(support_path, dpi=300, bbox_inches='tight')
        sample_paths['script_support'] = support_path
        plt.close(fig)
    else:
        plt.show()
    
    return sample_paths

def analyze_non_latin_support(font_path):
    """
    Analyze a font's support for non-Latin scripts.
    
    Args:
        font_path: Path to the font file.
        
    Returns:
        dict: Analysis of the font's script support.
    """
    try:
        font = TTFont(font_path)
        supported_scripts = detect_supported_scripts(font)
        
        # Count fully and partially supported scripts
        full_support = sum(1 for info in supported_scripts.values() if info['status'] == 'full')
        partial_support = sum(1 for info in supported_scripts.values() if info['status'] == 'partial')
        
        # Determine primary script
        primary_script = max(supported_scripts.items(), key=lambda x: x[1]['percentage'])[0]
        
        return {
            'supported_scripts': supported_scripts,
            'full_support_count': full_support,
            'partial_support_count': partial_support,
            'primary_script': primary_script
        }
    
    except Exception as e:
        print(f"Error analyzing non-Latin support: {e}")
        return {
            'error': str(e)
        }

def integrate_non_latin_analysis(font_info, font_path):
    """
    Integrate non-Latin script analysis into the main font_info dictionary.
    
    Args:
        font_info: Existing font_info dictionary from extract_font_properties.
        font_path: Path to the font file.
        
    Returns:
        dict: Updated font_info with non-Latin script data.
    """
    try:
        non_latin_info = analyze_non_latin_support(font_path)
        
        if 'error' in non_latin_info:
            font_info['non_latin_support'] = {
                'error': non_latin_info['error']
            }
        else:
            font_info['non_latin_support'] = non_latin_info
            
            # Add script support to personality description
            if 'personality' in font_info and 'emotional_description' in font_info['personality']:
                scripts_desc = ""
                if non_latin_info['full_support_count'] > 1:
                    scripts_desc = f" It has full support for {non_latin_info['full_support_count']} scripts, making it versatile for multilingual content."
                elif non_latin_info['primary_script'] != 'Latin':
                    scripts_desc = f" It is primarily designed for {non_latin_info['primary_script']} script."
                
                font_info['personality']['emotional_description'] += scripts_desc
            
            # Add multilingual capabilities to suitable use cases
            if 'personality' in font_info and 'suitable_use_cases' in font_info['personality']:
                if non_latin_info['full_support_count'] > 1:
                    font_info['personality']['suitable_use_cases']['suitable_for'].append("Multilingual publications")
                    font_info['personality']['suitable_use_cases']['suitable_for'].append("International websites")
                
                # Add specific script recommendations
                for script, info in non_latin_info['supported_scripts'].items():
                    if info['status'] == 'full' and script != 'Latin':
                        font_info['personality']['suitable_use_cases']['suitable_for'].append(f"{script} language content")
    
    except Exception as e:
        print(f"Error integrating non-Latin analysis: {e}")
    
    return font_info

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python non_latin_support.py <font_path>")
        sys.exit(1)
    
    font_path = sys.argv[1]
    
    # Analyze non-Latin support
    non_latin_info = analyze_non_latin_support(font_path)
    
    if 'error' in non_latin_info:
        print(f"Error: {non_latin_info['error']}")
        sys.exit(1)
    
    print("Non-Latin Script Support Analysis:")
    print(f"Primary script: {non_latin_info['primary_script']}")
    print(f"Fully supported scripts: {non_latin_info['full_support_count']}")
    print(f"Partially supported scripts: {non_latin_info['partial_support_count']}")
    
    print("\nDetailed Script Support:")
    for script, info in non_latin_info['supported_scripts'].items():
        print(f"{script}: {info['status']} ({info['percentage']:.1f}% - {info['supported_chars']}/{info['total_chars']} characters)")
    
    # Render script samples
    output_dir = "non_latin_visualizations"
    sample_paths = render_script_samples(font_path, non_latin_info['supported_scripts'], output_dir)
    
    if sample_paths:
        print(f"\nVisualizations saved to {output_dir}/:")
        for name, path in sample_paths.items():
            print(f"  {name}: {path}") 