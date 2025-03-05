#!/usr/bin/env python3
"""
Variable Font Support Module for Font Validator

This module provides functionality for analyzing and visualizing variable fonts.
It extends the Font Validator tool to handle the unique properties of variable fonts,
including axis information, design space analysis, and instance rendering.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil

def is_variable_font(font_path):
    """
    Check if a font is a variable font by examining its tables.
    
    Args:
        font_path (str): Path to the font file.
        
    Returns:
        bool: True if the font is a variable font, False otherwise.
    """
    try:
        font = TTFont(font_path)
        # Variable fonts must have 'fvar' table
        return 'fvar' in font
    except Exception as e:
        print(f"Error checking if font is variable: {e}")
        return False

def extract_variable_font_info(font_path):
    """
    Extract information about a variable font's axes and instances.
    
    Args:
        font_path (str): Path to the variable font file.
        
    Returns:
        dict: Information about the variable font's axes and named instances.
    """
    try:
        font = TTFont(font_path)
        
        if 'fvar' not in font:
            return {'is_variable': False, 'error': 'Not a variable font'}
        
        fvar = font['fvar']
        axes = {}
        
        # Extract axis information
        for axis in fvar.axes:
            axis_tag = axis.axisTag
            axes[axis_tag] = {
                'name': axis.axisNameID,
                'min_value': axis.minValue,
                'default_value': axis.defaultValue,
                'max_value': axis.maxValue
            }
            
            # Try to get the actual name from the name table
            if hasattr(font['name'], 'getDebugName'):
                axes[axis_tag]['name'] = font['name'].getDebugName(axis.axisNameID) or axis.axisTag
            else:
                # Fallback to common axis names
                common_names = {
                    'wght': 'Weight',
                    'wdth': 'Width',
                    'ital': 'Italic',
                    'slnt': 'Slant',
                    'opsz': 'Optical Size',
                    'GRAD': 'Grade',
                    'XTRA': 'X Transparency',
                    'XOPQ': 'X Opaque',
                    'YOPQ': 'Y Opaque',
                    'YTLC': 'Y Transparent Lowercase',
                    'YTUC': 'Y Transparent Uppercase'
                }
                axes[axis_tag]['name'] = common_names.get(axis_tag, axis_tag)
        
        # Extract named instances
        named_instances = []
        if hasattr(fvar, 'instances'):
            for instance in fvar.instances:
                instance_name = font['name'].getDebugName(instance.subfamilyNameID)
                coordinates = {axis.axisTag: instance.coordinates[i] for i, axis in enumerate(fvar.axes)}
                named_instances.append({
                    'name': instance_name,
                    'coordinates': coordinates
                })
        
        return {
            'is_variable': True,
            'axes': axes,
            'named_instances': named_instances
        }
    except Exception as e:
        print(f"Error extracting variable font info: {e}")
        return {'is_variable': False, 'error': str(e)}

def analyze_variable_font_design_space(font_path):
    """
    Analyze the design space of a variable font.
    
    Args:
        font_path (str): Path to the variable font file.
        
    Returns:
        dict: Analysis of the variable font's design space.
    """
    try:
        font = TTFont(font_path)
        
        if 'fvar' not in font:
            return {'is_variable': False, 'error': 'Not a variable font'}
        
        fvar = font['fvar']
        
        # Calculate design space size (number of possible combinations)
        design_space_size = 1
        axis_ranges = []
        
        for axis in fvar.axes:
            # Estimate number of meaningful steps for this axis
            # For continuous axes like weight, about 9 steps are meaningful
            # For binary axes like italic, only 2 steps are meaningful
            if axis.axisTag in ['ital']:
                steps = 2
            else:
                steps = 9
            
            design_space_size *= steps
            axis_ranges.append({
                'tag': axis.axisTag,
                'range': axis.maxValue - axis.minValue,
                'steps': steps
            })
        
        # Analyze axis interactions
        axis_interactions = []
        if len(fvar.axes) > 1:
            for i in range(len(fvar.axes)):
                for j in range(i+1, len(fvar.axes)):
                    axis1 = fvar.axes[i]
                    axis2 = fvar.axes[j]
                    axis_interactions.append({
                        'axis1': axis1.axisTag,
                        'axis2': axis2.axisTag,
                        'interaction_type': 'orthogonal'  # Most variable fonts have orthogonal axes
                    })
        
        # Check for STAT table which provides additional style attributes
        has_stat = 'STAT' in font
        
        return {
            'is_variable': True,
            'design_space_size': design_space_size,
            'axis_ranges': axis_ranges,
            'axis_interactions': axis_interactions,
            'has_stat_table': has_stat
        }
    except Exception as e:
        print(f"Error analyzing variable font design space: {e}")
        return {'is_variable': False, 'error': str(e)}

def visualize_variable_font_axes(font_path, output_dir=None):
    """
    Create visualizations of a variable font's axes.
    
    Args:
        font_path (str): Path to the variable font file.
        output_dir (str, optional): Directory to save visualizations.
        
    Returns:
        str: Path to the generated visualization file.
    """
    try:
        # Create output directory if it doesn't exist
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), 'font_visualizations')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Get variable font info
        var_info = extract_variable_font_info(font_path)
        
        if not var_info.get('is_variable', False):
            return None
        
        # Create a figure for the axes visualization
        fig, axes_plots = plt.subplots(len(var_info['axes']), 1, figsize=(10, 2 * len(var_info['axes'])))
        
        # Handle case with only one axis
        if len(var_info['axes']) == 1:
            axes_plots = [axes_plots]
        
        # Plot each axis
        for i, (axis_tag, axis_info) in enumerate(var_info['axes'].items()):
            ax = axes_plots[i]
            
            # Create a horizontal bar representing the axis range
            ax.set_xlim(axis_info['min_value'] - 0.1 * (axis_info['max_value'] - axis_info['min_value']),
                       axis_info['max_value'] + 0.1 * (axis_info['max_value'] - axis_info['min_value']))
            ax.set_ylim(0, 1)
            
            # Draw the axis line
            ax.plot([axis_info['min_value'], axis_info['max_value']], [0.5, 0.5], 'k-', linewidth=2)
            
            # Mark the default value
            ax.plot([axis_info['default_value']], [0.5], 'ro', markersize=10)
            
            # Add ticks for min, default, and max values
            ax.set_yticks([])
            ax.set_xticks([axis_info['min_value'], axis_info['default_value'], axis_info['max_value']])
            
            # Add labels
            ax.set_title(f"{axis_info['name']} ({axis_tag})")
            
            # Add named instances if available
            if 'named_instances' in var_info:
                instance_values = [instance['coordinates'].get(axis_tag, axis_info['default_value']) 
                                  for instance in var_info['named_instances']]
                instance_names = [instance['name'] for instance in var_info['named_instances']]
                
                # Plot instance markers
                for val, name in zip(instance_values, instance_names):
                    ax.plot([val], [0.5], 'bx', markersize=8)
                    ax.annotate(name, (val, 0.6), rotation=45, ha='right', fontsize=8)
        
        plt.tight_layout()
        
        # Save the visualization
        font_name = os.path.splitext(os.path.basename(font_path))[0]
        output_path = os.path.join(output_dir, f"{font_name}_variable_axes.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    except Exception as e:
        print(f"Error visualizing variable font axes: {e}")
        return None

def render_variable_font_samples(font_path, output_dir=None, sample_text="AaBbCcGgRr 0123"):
    """
    Render samples of a variable font at different axis settings.
    
    Args:
        font_path (str): Path to the variable font file.
        output_dir (str, optional): Directory to save visualizations.
        sample_text (str, optional): Text to render.
        
    Returns:
        str: Path to the generated visualization file.
    """
    try:
        # Create output directory if it doesn't exist
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), 'font_visualizations')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Get variable font info
        var_info = extract_variable_font_info(font_path)
        
        if not var_info.get('is_variable', False):
            return None
        
        # Create a temporary directory for font instances
        temp_dir = tempfile.mkdtemp()
        
        # Get the main axes to visualize (usually weight and width)
        main_axes = []
        for tag in ['wght', 'wdth']:
            if tag in var_info['axes']:
                main_axes.append(tag)
        
        # If we don't have the common axes, use the first two axes
        if not main_axes and len(var_info['axes']) > 0:
            main_axes = list(var_info['axes'].keys())[:min(2, len(var_info['axes']))]
        
        # If we have named instances, use those
        if 'named_instances' in var_info and var_info['named_instances']:
            instances = var_info['named_instances']
            
            # Create a grid of samples
            rows = int(np.ceil(np.sqrt(len(instances))))
            cols = int(np.ceil(len(instances) / rows))
            
            fig, axs = plt.subplots(rows, cols, figsize=(cols * 4, rows * 2))
            axs = axs.flatten() if isinstance(axs, np.ndarray) else [axs]
            
            for i, instance in enumerate(instances):
                if i < len(axs):
                    # Create an instance of the font
                    instance_path = os.path.join(temp_dir, f"instance_{i}.ttf")
                    font = TTFont(font_path)
                    instantiateVariableFont(font, instance['coordinates'])
                    font.save(instance_path)
                    
                    # Render text using PIL
                    img = Image.new('RGB', (500, 100), color='white')
                    draw = ImageDraw.Draw(img)
                    try:
                        pil_font = ImageFont.truetype(instance_path, 36)
                        draw.text((10, 10), sample_text, font=pil_font, fill='black')
                    except Exception as e:
                        draw.text((10, 10), f"Error: {str(e)}", fill='red')
                    
                    # Convert to numpy array for matplotlib
                    img_array = np.array(img)
                    
                    # Display in the subplot
                    axs[i].imshow(img_array)
                    axs[i].set_title(instance['name'])
                    axs[i].axis('off')
            
            # Hide unused subplots
            for i in range(len(instances), len(axs)):
                axs[i].axis('off')
        
        else:
            # If no named instances, create a grid of samples for the main axes
            if len(main_axes) == 1:
                # For one axis, create a linear series
                axis_tag = main_axes[0]
                axis_info = var_info['axes'][axis_tag]
                
                # Create 5 steps from min to max
                steps = 5
                values = np.linspace(axis_info['min_value'], axis_info['max_value'], steps)
                
                fig, axs = plt.subplots(steps, 1, figsize=(8, steps * 1.5))
                
                for i, val in enumerate(values):
                    # Create an instance of the font
                    instance_path = os.path.join(temp_dir, f"instance_{i}.ttf")
                    font = TTFont(font_path)
                    instantiateVariableFont(font, {axis_tag: val})
                    font.save(instance_path)
                    
                    # Render text using PIL
                    img = Image.new('RGB', (500, 100), color='white')
                    draw = ImageDraw.Draw(img)
                    try:
                        pil_font = ImageFont.truetype(instance_path, 36)
                        draw.text((10, 10), sample_text, font=pil_font, fill='black')
                    except Exception as e:
                        draw.text((10, 10), f"Error: {str(e)}", fill='red')
                    
                    # Convert to numpy array for matplotlib
                    img_array = np.array(img)
                    
                    # Display in the subplot
                    axs[i].imshow(img_array)
                    axs[i].set_title(f"{axis_info['name']}: {val:.1f}")
                    axs[i].axis('off')
            
            elif len(main_axes) >= 2:
                # For two axes, create a grid
                axis1_tag, axis2_tag = main_axes[:2]
                axis1_info = var_info['axes'][axis1_tag]
                axis2_info = var_info['axes'][axis2_tag]
                
                # Create 3x3 grid from min to max for each axis
                steps = 3
                values1 = np.linspace(axis1_info['min_value'], axis1_info['max_value'], steps)
                values2 = np.linspace(axis2_info['min_value'], axis2_info['max_value'], steps)
                
                fig, axs = plt.subplots(steps, steps, figsize=(steps * 3, steps * 2))
                
                for i, val1 in enumerate(values1):
                    for j, val2 in enumerate(values2):
                        # Create an instance of the font
                        instance_path = os.path.join(temp_dir, f"instance_{i}_{j}.ttf")
                        font = TTFont(font_path)
                        instantiateVariableFont(font, {axis1_tag: val1, axis2_tag: val2})
                        font.save(instance_path)
                        
                        # Render text using PIL
                        img = Image.new('RGB', (500, 100), color='white')
                        draw = ImageDraw.Draw(img)
                        try:
                            pil_font = ImageFont.truetype(instance_path, 36)
                            draw.text((10, 10), sample_text, font=pil_font, fill='black')
                        except Exception as e:
                            draw.text((10, 10), f"Error: {str(e)}", fill='red')
                        
                        # Convert to numpy array for matplotlib
                        img_array = np.array(img)
                        
                        # Display in the subplot
                        axs[i, j].imshow(img_array)
                        axs[i, j].set_title(f"{axis1_tag}: {val1:.1f}, {axis2_tag}: {val2:.1f}", fontsize=8)
                        axs[i, j].axis('off')
        
        plt.tight_layout()
        
        # Save the visualization
        font_name = os.path.splitext(os.path.basename(font_path))[0]
        output_path = os.path.join(output_dir, f"{font_name}_variable_samples.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return output_path
    except Exception as e:
        print(f"Error rendering variable font samples: {e}")
        # Clean up temporary directory if it exists
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        return None

def integrate_variable_font_analysis(font_info, font_path):
    """
    Integrate variable font analysis into the font_info dictionary.
    
    Args:
        font_info (dict): Existing font information dictionary.
        font_path (str): Path to the font file.
        
    Returns:
        dict: Updated font information dictionary with variable font data.
    """
    try:
        # Check if the font is a variable font
        if not is_variable_font(font_path):
            return font_info
        
        # Extract variable font information
        var_info = extract_variable_font_info(font_path)
        
        if not var_info.get('is_variable', False):
            return font_info
        
        # Analyze design space
        design_space = analyze_variable_font_design_space(font_path)
        
        # Add variable font information to font_info
        font_info['is_variable_font'] = True
        font_info['variable_font_info'] = var_info
        font_info['variable_design_space'] = design_space
        
        # Update the font description to mention it's a variable font
        if 'personality' in font_info and 'emotional_description' in font_info['personality']:
            font_info['personality']['emotional_description'] = (
                "This variable font " + font_info['personality']['emotional_description'].lower()
            )
        
        # Add variable font specific use cases
        if 'personality' in font_info and 'use_cases' in font_info['personality']:
            font_info['personality']['use_cases'].append("Responsive web design")
            font_info['personality']['use_cases'].append("User interfaces with adjustable text settings")
            font_info['personality']['use_cases'].append("Designs requiring subtle typographic variations")
        
        return font_info
    except Exception as e:
        print(f"Error integrating variable font analysis: {e}")
        return font_info

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python variable_font_support.py <font_path> [output_dir]")
        sys.exit(1)
    
    font_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not is_variable_font(font_path):
        print(f"The font '{font_path}' is not a variable font.")
        sys.exit(1)
    
    print(f"Analyzing variable font: {font_path}")
    
    var_info = extract_variable_font_info(font_path)
    print("\nVariable Font Information:")
    print(f"Axes: {', '.join(var_info['axes'].keys())}")
    for axis_tag, axis_info in var_info['axes'].items():
        print(f"  {axis_info['name']} ({axis_tag}): {axis_info['min_value']} to {axis_info['max_value']} (default: {axis_info['default_value']})")
    
    if 'named_instances' in var_info:
        print("\nNamed Instances:")
        for instance in var_info['named_instances']:
            print(f"  {instance['name']}: {instance['coordinates']}")
    
    design_space = analyze_variable_font_design_space(font_path)
    print("\nDesign Space Analysis:")
    print(f"Design Space Size: {design_space['design_space_size']} combinations")
    
    print("\nGenerating visualizations...")
    axes_viz = visualize_variable_font_axes(font_path, output_dir)
    samples_viz = render_variable_font_samples(font_path, output_dir)
    
    if axes_viz:
        print(f"Axes visualization saved to: {axes_viz}")
    if samples_viz:
        print(f"Samples visualization saved to: {samples_viz}") 