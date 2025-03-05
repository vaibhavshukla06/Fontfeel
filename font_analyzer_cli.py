#!/usr/bin/env python3
"""
Font Analyzer CLI - A command-line tool to analyze font properties.
Supports TrueType (.ttf), OpenType (.otf), WOFF, and WOFF2 formats.
"""

import argparse
import os
import json
from font_validator import extract_font_properties, visualize_font_properties, create_font_report

# Check if variable font support is available
try:
    from variable_font_support import is_variable_font
    VARIABLE_FONT_SUPPORT = True
except ImportError:
    VARIABLE_FONT_SUPPORT = False

# Supported font formats
SUPPORTED_FORMATS = ['.ttf', '.otf', '.woff', '.woff2']

def main():
    parser = argparse.ArgumentParser(description='Analyze font files and extract properties. Supports TrueType (.ttf), OpenType (.otf), WOFF, and WOFF2 formats.')
    
    # Create a mutually exclusive group for the main action
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument('--help-formats', action='store_true', 
                        help='Display information about supported font formats')
    action_group.add_argument('font_path', nargs='?', help='Path to the font file or directory containing font files')
    
    # Other options
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--output', '-o', help='Save results to a file')
    parser.add_argument('--format', choices=['ttf', 'otf', 'woff', 'woff2', 'all'], default='all',
                        help='Specify font format to process (default: all)')
    
    # Visualization options
    visualization_group = parser.add_argument_group('Visualization Options')
    visualization_group.add_argument('--visualize', '-v', action='store_true', 
                                    help='Generate visualizations of font properties')
    visualization_group.add_argument('--viz-dir', default='font_visualizations',
                                    help='Directory to save visualizations (default: font_visualizations)')
    visualization_group.add_argument('--report', '-r', action='store_true',
                                    help='Generate a comprehensive HTML report with visualizations')
    visualization_group.add_argument('--report-dir', default='font_reports',
                                    help='Directory to save reports (default: font_reports)')
    
    # Variable font options (only if support is available)
    if VARIABLE_FONT_SUPPORT:
        variable_font_group = parser.add_argument_group('Variable Font Options')
        variable_font_group.add_argument('--variable-only', action='store_true',
                                        help='Only process variable fonts')
        variable_font_group.add_argument('--var-samples', action='store_true',
                                        help='Generate sample renderings for variable fonts')
    
    args = parser.parse_args()
    
    # Show help about supported formats if requested
    if args.help_formats:
        print_format_help()
        return 0
    
    # Check if font_path is provided
    if not args.font_path:
        parser.print_help()
        return 1
    
    # Filter formats based on user selection
    if args.format != 'all':
        selected_formats = [f'.{args.format}']
    else:
        selected_formats = SUPPORTED_FORMATS
    
    # Check if the path exists
    if not os.path.exists(args.font_path):
        print(f"Error: Path '{args.font_path}' does not exist.")
        return 1
    
    results = []
    
    # Process a single font file
    if os.path.isfile(args.font_path):
        file_ext = os.path.splitext(args.font_path)[1].lower()
        if file_ext not in selected_formats:
            print(f"Warning: '{args.font_path}' does not appear to be a supported font file ({', '.join(selected_formats)}).")
        
        # Check if it's a variable font if --variable-only is specified
        if VARIABLE_FONT_SUPPORT and hasattr(args, 'variable_only') and args.variable_only:
            if not is_variable_font(args.font_path):
                print(f"Skipping '{args.font_path}' as it is not a variable font.")
                return 0
        
        font_info = extract_font_properties(args.font_path)
        if font_info:
            # Store the font path for visualization
            font_info['font_path'] = args.font_path
            
            results.append({
                'file': args.font_path,
                'info': font_info
            })
            
            if not args.json:
                print_font_info(args.font_path, font_info)
            
            # Generate visualizations if requested
            if args.visualize:
                print(f"\nGenerating visualizations for {os.path.basename(args.font_path)}...")
                viz_paths = visualize_font_properties(font_info, args.viz_dir)
                print(f"Visualizations saved to {args.viz_dir}/")
            
            # Generate report if requested
            if args.report:
                print(f"\nGenerating report for {os.path.basename(args.font_path)}...")
                report_path = create_font_report(font_info, args.report_dir)
                print(f"Report saved to {report_path}")
    
    # Process a directory of font files
    elif os.path.isdir(args.font_path):
        font_files = []
        for root, _, files in os.walk(args.font_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in selected_formats):
                    font_files.append(os.path.join(root, file))
        
        if not font_files:
            print(f"No supported font files ({', '.join(selected_formats)}) found in '{args.font_path}'.")
            return 1
        
        for font_file in font_files:
            # Check if it's a variable font if --variable-only is specified
            if VARIABLE_FONT_SUPPORT and hasattr(args, 'variable_only') and args.variable_only:
                if not is_variable_font(font_file):
                    print(f"Skipping '{font_file}' as it is not a variable font.")
                    continue
            
            font_info = extract_font_properties(font_file)
            if font_info:
                # Store the font path for visualization
                font_info['font_path'] = font_file
                
                results.append({
                    'file': font_file,
                    'info': font_info
                })
                
                if not args.json:
                    print_font_info(font_file, font_info)
                    print("-" * 50)
                
                # Generate visualizations if requested
                if args.visualize:
                    print(f"Generating visualizations for {os.path.basename(font_file)}...")
                    viz_paths = visualize_font_properties(font_info, args.viz_dir)
                
                # Generate report if requested
                if args.report:
                    print(f"Generating report for {os.path.basename(font_file)}...")
                    report_path = create_font_report(font_info, args.report_dir)
        
        if args.visualize:
            print(f"\nAll visualizations saved to {args.viz_dir}/")
        
        if args.report:
            print(f"\nAll reports saved to {args.report_dir}/")
    
    # Output results in JSON format if requested
    if args.json:
        json_output = json.dumps(results, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
        else:
            print(json_output)
    # Save results to a file if requested
    elif args.output:
        with open(args.output, 'w') as f:
            for result in results:
                write_font_info_to_file(f, result['file'], result['info'])
    
    return 0

def print_format_help():
    """Print information about supported font formats."""
    print("\nSupported Font Formats:")
    print("----------------------")
    print("TrueType (.ttf):")
    print("  - The most common font format")
    print("  - Contains TrueType outlines in the 'glyf' table")
    print("  - Full analysis of stroke width, shape, and other features")
    print()
    print("OpenType with TrueType outlines (.otf):")
    print("  - OpenType fonts that use TrueType outlines")
    print("  - Contains TrueType outlines in the 'glyf' table")
    print("  - Full analysis similar to TrueType fonts")
    print()
    print("OpenType with CFF outlines (.otf):")
    print("  - OpenType fonts that use PostScript/CFF outlines")
    print("  - Contains outlines in the 'CFF ' table instead of 'glyf'")
    print("  - Some features like stroke width are estimated rather than measured directly")
    print()
    print("WOFF (.woff) and WOFF2 (.woff2):")
    print("  - Web Open Font Format (compressed fonts for web use)")
    print("  - Same analysis capabilities as the underlying font format")

def print_font_info(font_path, font_info):
    """Print font information in a readable format."""
    print(f"\nFont: {font_path}")
    print(f"Font Name: {font_info['font_name']}")
    print(f"Format: {font_info['format']}")
    print(f"Style: {font_info['style']}")
    
    # Weight information
    print(f"Weight (from OS/2): {font_info['weight']['description']} ({font_info['weight']['class']})")
    
    # Stroke width information
    if font_info['weight']['stroke_width'] is not None:
        print(f"Stroke Width: {font_info['weight']['stroke_width']:.2f} units")
        print(f"Normalized Stroke Width: {font_info['weight']['normalized_stroke_width']:.4f}")
        print(f"Weight (by stroke): {font_info['weight']['weight_by_stroke']}")
        if 'is_estimated' in font_info['weight'] and font_info['weight']['is_estimated']:
            print(f"Note: Stroke width is estimated using {font_info['weight']['estimation_method']}")
    else:
        print("Stroke Width: Could not be measured")
    
    # Width information
    print(f"Width (from OS/2): {font_info['width']['description']} ({font_info['width']['class']})")
    
    # Aspect ratio information
    if font_info['width']['aspect_ratio'] is not None:
        print(f"Aspect Ratio: {font_info['width']['aspect_ratio']:.2f}")
        print(f"Width (by aspect): {font_info['width']['width_by_aspect']}")
    else:
        print("Aspect Ratio: Could not be measured")
    
    print(f"Shape: {font_info['shape']['type']}")
    if 'is_estimated' in font_info['shape'] and font_info['shape']['is_estimated']:
        print(f"Note: Shape is estimated using {font_info['shape']['estimation_method']}")
    
    print(f"Spacing: {font_info['spacing']['width_type']} width, {font_info['spacing']['spacing_type']} spacing")
    
    # Vertical metrics information
    if 'vertical_metrics' in font_info and 'error' not in font_info['vertical_metrics']:
        print("\nVertical Metrics:")
        vm = font_info['vertical_metrics']
        
        if 'x_height' in vm:
            print(f"  x-height: {vm['x_height']:.2f} units ({vm['normalized_x_height']:.4f} normalized)")
        
        if 'cap_height' in vm:
            print(f"  Cap height: {vm['cap_height']:.2f} units ({vm['normalized_cap_height']:.4f} normalized)")
        
        if 'x_to_cap_ratio' in vm:
            print(f"  x-height to cap-height ratio: {vm['x_to_cap_ratio']:.2f}")
            if 'x_height_class' in vm:
                print(f"  x-height classification: {vm['x_height_class']}")
        
        if 'ascender' in vm and 'descender' in vm:
            print(f"  Ascender: {vm['ascender']:.2f} units ({vm['normalized_ascender']:.4f} normalized)")
            print(f"  Descender: {abs(vm['descender']):.2f} units ({vm['normalized_descender']:.4f} normalized)")
            print(f"  Total height: {vm['total_height']:.2f} units")
            print(f"  Ascender/descender ratio: {vm['ascender_ratio']:.2f}/{vm['descender_ratio']:.2f}")
    
    # Contrast information
    if 'contrast' in font_info and font_info['contrast']['contrast_ratio'] is not None:
        print("\nStroke Contrast:")
        print(f"  Contrast ratio: {font_info['contrast']['contrast_ratio']:.2f}")
        print(f"  Contrast type: {font_info['contrast']['contrast_type']}")
        if 'sample_size' in font_info['contrast']:
            print(f"  Sample size: {font_info['contrast']['sample_size']} glyphs")
    
    # Personality analysis
    if 'personality' in font_info:
        print("\nPersonality Analysis:")
        
        # Print emotional description
        if 'emotional_description' in font_info['personality']:
            print(f"Emotional Description: {font_info['personality']['emotional_description']}")
        
        # Print dominant traits
        if 'dominant_traits' in font_info['personality']:
            print("\nDominant Traits:")
            for trait, value in font_info['personality']['dominant_traits']:
                print(f"  - {trait.capitalize()}: {value:.1f}")
        
        # Print suitable use cases
        if 'suitable_use_cases' in font_info['personality']:
            use_cases = font_info['personality']['suitable_use_cases']
            
            if 'suitable_for' in use_cases and use_cases['suitable_for']:
                print("\nSuitable For:")
                for use_case in use_cases['suitable_for'][:5]:  # Limit to top 5
                    print(f"  - {use_case}")
            
            if 'less_suitable_for' in use_cases and use_cases['less_suitable_for']:
                print("\nLess Suitable For:")
                for use_case in use_cases['less_suitable_for'][:3]:  # Limit to top 3
                    print(f"  - {use_case}")
    
    print()

def write_font_info_to_file(file, font_path, font_info):
    """Write font information to a file in a readable format."""
    file.write(f"\nFont: {font_path}\n")
    file.write(f"Font Name: {font_info['font_name']}\n")
    file.write(f"Format: {font_info['format']}\n")
    file.write(f"Style: {font_info['style']}\n")
    
    # Weight information
    file.write(f"Weight (from OS/2): {font_info['weight']['description']} ({font_info['weight']['class']})\n")
    
    # Stroke width information
    if font_info['weight']['stroke_width'] is not None:
        file.write(f"Stroke Width: {font_info['weight']['stroke_width']:.2f} units\n")
        file.write(f"Normalized Stroke Width: {font_info['weight']['normalized_stroke_width']:.4f}\n")
        file.write(f"Weight (by stroke): {font_info['weight']['weight_by_stroke']}\n")
        if 'is_estimated' in font_info['weight'] and font_info['weight']['is_estimated']:
            file.write(f"Note: Stroke width is estimated using {font_info['weight']['estimation_method']}\n")
    else:
        file.write("Stroke Width: Could not be measured\n")
    
    # Width information
    file.write(f"Width (from OS/2): {font_info['width']['description']} ({font_info['width']['class']})\n")
    
    # Aspect ratio information
    if font_info['width']['aspect_ratio'] is not None:
        file.write(f"Aspect Ratio: {font_info['width']['aspect_ratio']:.2f}\n")
        file.write(f"Width (by aspect): {font_info['width']['width_by_aspect']}\n")
    else:
        file.write("Aspect Ratio: Could not be measured\n")
    
    file.write(f"Shape: {font_info['shape']['type']}\n")
    if 'is_estimated' in font_info['shape'] and font_info['shape']['is_estimated']:
        file.write(f"Note: Shape is estimated using {font_info['shape']['estimation_method']}\n")
    
    file.write(f"Spacing: {font_info['spacing']['width_type']} width, {font_info['spacing']['spacing_type']} spacing\n")
    
    # Vertical metrics information
    if 'vertical_metrics' in font_info and 'error' not in font_info['vertical_metrics']:
        file.write("\nVertical Metrics:\n")
        vm = font_info['vertical_metrics']
        
        if 'x_height' in vm:
            file.write(f"  x-height: {vm['x_height']:.2f} units ({vm['normalized_x_height']:.4f} normalized)\n")
        
        if 'cap_height' in vm:
            file.write(f"  Cap height: {vm['cap_height']:.2f} units ({vm['normalized_cap_height']:.4f} normalized)\n")
        
        if 'x_to_cap_ratio' in vm:
            file.write(f"  x-height to cap-height ratio: {vm['x_to_cap_ratio']:.2f}\n")
            if 'x_height_class' in vm:
                file.write(f"  x-height classification: {vm['x_height_class']}\n")
        
        if 'ascender' in vm and 'descender' in vm:
            file.write(f"  Ascender: {vm['ascender']:.2f} units ({vm['normalized_ascender']:.4f} normalized)\n")
            file.write(f"  Descender: {abs(vm['descender']):.2f} units ({vm['normalized_descender']:.4f} normalized)\n")
            file.write(f"  Total height: {vm['total_height']:.2f} units\n")
            file.write(f"  Ascender/descender ratio: {vm['ascender_ratio']:.2f}/{vm['descender_ratio']:.2f}\n")
    
    # Contrast information
    if 'contrast' in font_info and font_info['contrast']['contrast_ratio'] is not None:
        file.write("\nStroke Contrast:\n")
        file.write(f"  Contrast ratio: {font_info['contrast']['contrast_ratio']:.2f}\n")
        file.write(f"  Contrast type: {font_info['contrast']['contrast_type']}\n")
        if 'sample_size' in font_info['contrast']:
            file.write(f"  Sample size: {font_info['contrast']['sample_size']} glyphs\n")
    
    # Personality analysis
    if 'personality' in font_info:
        file.write("\nPersonality Analysis:\n")
        
        # Write emotional description
        if 'emotional_description' in font_info['personality']:
            file.write(f"Emotional Description: {font_info['personality']['emotional_description']}\n")
        
        # Write dominant traits
        if 'dominant_traits' in font_info['personality']:
            file.write("\nDominant Traits:\n")
            for trait, value in font_info['personality']['dominant_traits']:
                file.write(f"  - {trait.capitalize()}: {value:.1f}\n")
        
        # Write suitable use cases
        if 'suitable_use_cases' in font_info['personality']:
            use_cases = font_info['personality']['suitable_use_cases']
            
            if 'suitable_for' in use_cases and use_cases['suitable_for']:
                file.write("\nSuitable For:\n")
                for use_case in use_cases['suitable_for'][:5]:  # Limit to top 5
                    file.write(f"  - {use_case}\n")
            
            if 'less_suitable_for' in use_cases and use_cases['less_suitable_for']:
                file.write("\nLess Suitable For:\n")
                for use_case in use_cases['less_suitable_for'][:3]:  # Limit to top 3
                    file.write(f"  - {use_case}\n")
    
    file.write("\n")

if __name__ == "__main__":
    exit(main()) 