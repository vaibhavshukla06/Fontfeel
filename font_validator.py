from fontTools.ttLib import TTFont
import numpy as np
import math
from collections import defaultdict
import os

def determine_font_style(font):
    """
    Determines if a font is serif, sans-serif, script, or decorative by analyzing glyph features.
    Supports both TrueType (glyf) and OpenType (CFF) outlines.
    
    Args:
        font: A TTFont object.
    
    Returns:
        str: The style of the font ('serif', 'sans-serif', 'script', 'decorative', 'monospace', or 'unknown').
    """
    try:
        # First check if we can determine from the font name
        name_table = font['name'].getName(1, 3, 1, 1033)  # Font family name (Windows, English US)
        if name_table:
            family_name = name_table.toStr().lower()
            
            # Check for explicit style indicators in the name
            if "roboto" in family_name or "sans" in family_name and "serif" not in family_name:
                return "sans-serif"
            elif "serif" in family_name and "sans" not in family_name:
                return "serif"
            elif any(term in family_name for term in ["script", "handwriting", "cursive", "brush", "pacifico", "dancing"]):
                return "script"
            elif any(term in family_name for term in ["deco", "display", "ornament", "fancy", "elite", "special"]):
                return "decorative"
        
        # If we can't determine from the name, check OS/2 panose classification
        if 'OS/2' in font and hasattr(font['OS/2'], 'panose'):
            panose = font['OS/2'].panose
            # Check panose.bFamilyType and panose.bSerifStyle
            if panose.bFamilyType == 2:  # Text and Display
                if panose.bSerifStyle == 11 or panose.bSerifStyle == 0:
                    return "sans-serif"
                elif panose.bSerifStyle > 1 and panose.bSerifStyle < 15:
                    return "serif"
            elif panose.bFamilyType == 3:
                return "script"
            elif panose.bFamilyType == 4:
                return "decorative"
        
        # Check if monospaced by examining post table
        if hasattr(font['post'], 'isFixedPitch') and font['post'].isFixedPitch:
            return "monospace"
        
        # Get the cmap to map Unicode values to glyph names
        cmap = font.getBestCmap()
        if not cmap:
            return "unknown"
        
        # Check for key glyphs that help distinguish font styles
        key_chars = ['I', 'a', 'o', 'g', 'e']
        key_unicodes = [ord(char) for char in key_chars]
        
        # Get glyph names for these characters
        glyph_names = [cmap.get(unicode_val) for unicode_val in key_unicodes if unicode_val in cmap]
        
        if not glyph_names:
            return "unknown"
        
        # For TrueType fonts, analyze glyph features
        if 'glyf' in font:
            # Analyze glyph features
            serif_score = 0
            script_score = 0
            decorative_score = 0
            
            for glyph_name in glyph_names:
                if not glyph_name or glyph_name not in font['glyf']:
                    continue
                    
                glyph = font['glyf'][glyph_name]
                
                # Skip empty glyphs
                if glyph.numberOfContours <= 0:
                    continue
                
                # Check for serif features
                serif_score += has_serif_features(glyph)
                
                # Check for script features (connected, flowing strokes)
                script_score += has_script_features(glyph)
                
                # Check for decorative features (complex, ornate)
                decorative_score += has_decorative_features(glyph)
            
            # Determine style based on scores
            if script_score >= 3 and script_score > serif_score and script_score > decorative_score:
                return "script"
            elif decorative_score >= 3 and decorative_score > serif_score:
                return "decorative"
            elif serif_score >= 2 and serif_score > script_score:
                return "serif"
            else:
                return "sans-serif"
        
        # For OpenType CFF fonts, rely on metadata
        elif 'CFF ' in font or 'CFF2' in font:
            # Try to determine from CFF data
            cff_table = font['CFF '] if 'CFF ' in font else font['CFF2']
            
            # Check if we have a font name in the CFF table
            if hasattr(cff_table, 'cff') and hasattr(cff_table.cff, 'fontNames') and cff_table.cff.fontNames:
                cff_font_name = cff_table.cff.fontNames[0].lower()
                
                # Check for style indicators in the CFF font name
                if "serif" in cff_font_name and "sans" not in cff_font_name:
                    return "serif"
                elif "sans" in cff_font_name:
                    return "sans-serif"
                elif any(term in cff_font_name for term in ["script", "brush", "hand"]):
                    return "script"
                elif any(term in cff_font_name for term in ["deco", "display", "ornament"]):
                    return "decorative"
            
            # If we couldn't determine from CFF data, use a fallback approach
            # For OpenType fonts, we'll rely more on the OS/2 table
            if 'OS/2' in font:
                # Check IBM font class
                if hasattr(font['OS/2'], 'sFamilyClass'):
                    family_class = font['OS/2'].sFamilyClass
                    class_id = family_class >> 8
                    subclass_id = family_class & 0xFF
                    
                    if class_id == 1 or class_id == 2:  # Old Style or Transitional
                        return "serif"
                    elif class_id == 3 or class_id == 4:  # Modern or Clarendon
                        return "serif"
                    elif class_id == 5:  # Slab Serif
                        return "serif"
                    elif class_id == 8:  # Sans Serif
                        return "sans-serif"
                    elif class_id == 9:  # Ornamentals
                        return "decorative"
                    elif class_id == 10:  # Scripts
                        return "script"
            
            # Default to sans-serif if we couldn't determine
            return "sans-serif"
        
        # If we can't determine, default to sans-serif
        return "sans-serif"
            
    except Exception as e:
        print(f"Error determining font style: {e}")
        return "unknown"

def has_serif_features(glyph):
    """
    Checks if a glyph has serif-like features.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        
    Returns:
        int: A score indicating the likelihood of serif features (0-2).
    """
    # Serifs often have small protrusions at the ends of strokes
    # We can detect this by looking at the complexity of the glyph
    
    # Simple heuristic: Serifs typically have more contours and points
    if glyph.numberOfContours > 1:
        # Check if the glyph has coordinates
        if hasattr(glyph, 'coordinates') and len(glyph.coordinates) > 0:
            # More complex glyphs with many points are more likely to have serifs
            if len(glyph.coordinates) > 20:
                return 2
            elif len(glyph.coordinates) > 12:
                return 1
    
    return 0

def has_script_features(glyph):
    """
    Checks if a glyph has script-like features (flowing, connected strokes).
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        
    Returns:
        int: A score indicating the likelihood of script features (0-2).
    """
    # Script fonts typically have flowing, connected strokes
    # They often have fewer contours but more complex curves
    
    if hasattr(glyph, 'coordinates') and len(glyph.coordinates) > 0:
        # Script fonts often have fewer contours but more points per contour
        if glyph.numberOfContours == 1 and len(glyph.coordinates) > 20:
            return 2
        # Also check for asymmetry, which is common in script fonts
        elif is_asymmetric(glyph) and glyph.numberOfContours <= 2:
            return 1
    
    return 0

def has_decorative_features(glyph):
    """
    Checks if a glyph has decorative features (ornate, complex).
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        
    Returns:
        int: A score indicating the likelihood of decorative features (0-2).
    """
    # Decorative fonts often have very complex glyphs with many contours and points
    
    if glyph.numberOfContours > 3:
        if hasattr(glyph, 'coordinates') and len(glyph.coordinates) > 0:
            # Very complex glyphs are likely decorative
            if len(glyph.coordinates) > 30:
                return 2
            elif len(glyph.coordinates) > 20:
                return 1
    
    return 0

def is_asymmetric(glyph):
    """
    Checks if a glyph is asymmetric, which is common in script fonts.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        
    Returns:
        bool: True if the glyph appears asymmetric.
    """
    # Simple heuristic: Check if points are distributed unevenly
    if hasattr(glyph, 'coordinates') and len(glyph.coordinates) > 0:
        x_coords = [coord[0] for coord in glyph.coordinates]
        if x_coords:
            min_x = min(x_coords)
            max_x = max(x_coords)
            mid_x = (min_x + max_x) / 2
            
            # Count points on left and right sides
            left_points = sum(1 for x in x_coords if x < mid_x)
            right_points = sum(1 for x in x_coords if x > mid_x)
            
            # If there's a significant imbalance, it's likely asymmetric
            if left_points > right_points * 1.5 or right_points > left_points * 1.5:
                return True
    
    return False

def calculate_stroke_width(font):
    """
    Calculates the average stroke width of a font and classifies its weight.
    Supports both TrueType (glyf) and OpenType (CFF) outlines.
    
    Args:
        font: A TTFont object.
    
    Returns:
        dict: Information about the stroke width and weight classification.
    """
    try:
        # Get units per em from the head table
        units_per_em = font['head'].unitsPerEm
        
        # Get the cmap to map Unicode values to glyph names
        cmap = font.getBestCmap()
        if not cmap:
            return {
                'stroke_width': None,
                'normalized_stroke_width': None,
                'weight_by_stroke': 'unknown',
                'reason': 'No cmap table found'
            }
        
        # Sample glyphs for stroke width analysis
        # We'll use uppercase and lowercase letters with vertical and horizontal strokes
        sample_chars = ['H', 'I', 'O', 'n', 'o', 'l']
        sample_unicodes = [ord(char) for char in sample_chars]
        
        # Get glyph names for these characters
        glyph_names = [cmap.get(unicode_val) for unicode_val in sample_unicodes if unicode_val in cmap]
        
        if not glyph_names:
            return {
                'stroke_width': None,
                'normalized_stroke_width': None,
                'weight_by_stroke': 'unknown',
                'reason': 'No sample glyphs found'
            }
        
        # Collect stroke width measurements
        stroke_widths = []
        
        # Check if the font has TrueType outlines (glyf table)
        if 'glyf' in font:
            for glyph_name in glyph_names:
                if not glyph_name or glyph_name not in font['glyf']:
                    continue
                    
                glyph = font['glyf'][glyph_name]
                
                # Skip empty glyphs
                if glyph.numberOfContours <= 0:
                    continue
                
                # Measure stroke width for this glyph
                stroke_width = measure_glyph_stroke_width(glyph)
                if stroke_width is not None and stroke_width > 0:
                    stroke_widths.append(stroke_width)
        
        # Check if the font has OpenType CFF outlines
        elif 'CFF ' in font or 'CFF2' in font:
            # For CFF fonts, we'll use an alternative approach
            # We can estimate stroke width from OS/2 weight class
            weight_class = font['OS/2'].usWeightClass
            
            # Estimate normalized stroke width based on weight class
            # These are approximate values and can be refined with more testing
            estimated_normalized_width = weight_class / 9000  # Rough approximation
            
            # Create a synthetic stroke width
            synthetic_stroke_width = estimated_normalized_width * units_per_em
            
            return {
                'stroke_width': synthetic_stroke_width,
                'normalized_stroke_width': estimated_normalized_width,
                'weight_by_stroke': classify_weight_by_value(weight_class),
                'is_estimated': True,
                'estimation_method': 'OS/2 weight class'
            }
        else:
            return {
                'stroke_width': None,
                'normalized_stroke_width': None,
                'weight_by_stroke': 'unknown',
                'reason': 'Unsupported outline format'
            }
        
        if not stroke_widths:
            return {
                'stroke_width': None,
                'normalized_stroke_width': None,
                'weight_by_stroke': 'unknown',
                'reason': 'Could not measure stroke widths'
            }
        
        # Calculate average stroke width
        average_stroke_width = sum(stroke_widths) / len(stroke_widths)
        
        # Normalize stroke width relative to units per em
        normalized_stroke_width = average_stroke_width / units_per_em
        
        # Classify weight based on normalized stroke width
        # These thresholds can be adjusted based on testing with various fonts
        weight_class = classify_weight_by_normalized_stroke(normalized_stroke_width)
        
        return {
            'stroke_width': average_stroke_width,
            'normalized_stroke_width': normalized_stroke_width,
            'weight_by_stroke': weight_class
        }
        
    except Exception as e:
        return {
            'stroke_width': None,
            'normalized_stroke_width': None,
            'weight_by_stroke': 'error',
            'reason': str(e)
        }

def classify_weight_by_normalized_stroke(normalized_stroke_width):
    """
    Classifies font weight based on normalized stroke width.
    
    Args:
        normalized_stroke_width (float): Stroke width normalized by units per em.
    
    Returns:
        str: Weight classification.
    """
    if normalized_stroke_width < 0.05:
        return "thin"
    elif normalized_stroke_width < 0.07:
        return "light"
    elif normalized_stroke_width < 0.09:
        return "regular"
    elif normalized_stroke_width < 0.12:
        return "medium"
    elif normalized_stroke_width < 0.15:
        return "bold"
    elif normalized_stroke_width < 0.18:
        return "extra bold"
    else:
        return "black"

def classify_weight_by_value(weight_value):
    """
    Classifies font weight based on OS/2 usWeightClass value.
    
    Args:
        weight_value (int): OS/2 usWeightClass value.
    
    Returns:
        str: Weight classification.
    """
    if weight_value <= 150:
        return "thin"
    elif weight_value <= 250:
        return "extra light"
    elif weight_value <= 350:
        return "light"
    elif weight_value <= 450:
        return "regular"
    elif weight_value <= 550:
        return "medium"
    elif weight_value <= 650:
        return "semi bold"
    elif weight_value <= 750:
        return "bold"
    elif weight_value <= 850:
        return "extra bold"
    else:
        return "black"

def measure_glyph_stroke_width(glyph):
    """
    Measures the stroke width of a glyph using advanced contour analysis techniques.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
    
    Returns:
        float: The estimated stroke width of the glyph, or None if it couldn't be measured.
    """
    try:
        # Check if the glyph has coordinates
        if not hasattr(glyph, 'coordinates') or len(glyph.coordinates) == 0:
            return None
        
        # Get the bounding box of the glyph
        x_coords = [coord[0] for coord in glyph.coordinates]
        y_coords = [coord[1] for coord in glyph.coordinates]
        
        if not x_coords or not y_coords:
            return None
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        width = x_max - x_min
        height = y_max - y_min
        
        # Skip glyphs that are too small or have zero dimensions
        if width <= 0 or height <= 0:
            return None
        
        # Get flags to identify on-curve and off-curve points
        if not hasattr(glyph, 'flags'):
            return None
            
        flags = glyph.flags
        coordinates = glyph.coordinates
        
        if len(coordinates) != len(flags):
            return None
        
        # Identify the glyph type to use the most appropriate measurement method
        glyph_type = identify_glyph_type(glyph, width, height)
        
        # Method 1: For vertical strokes (like in 'I', 'l')
        if glyph_type == "vertical_stroke":
            return measure_vertical_stroke_width(glyph, width, height)
        
        # Method 2: For horizontal strokes (like in 'E', '_')
        elif glyph_type == "horizontal_stroke":
            return measure_horizontal_stroke_width(glyph, width, height)
        
        # Method 3: For circular glyphs with inner and outer contours (like 'O', 'o')
        elif glyph_type == "circular" and glyph.numberOfContours == 2:
            return measure_circular_glyph_stroke_width(glyph, coordinates, flags)
        
        # Method 4: For complex glyphs, use contour distance analysis
        elif glyph_type == "complex":
            return measure_complex_glyph_stroke_width(glyph, coordinates, flags)
        
        # Method 5: Fallback to improved area-to-perimeter ratio
        return measure_area_perimeter_stroke_width(glyph, width, height)
        
    except Exception as e:
        print(f"Error measuring glyph stroke width: {e}")
        return None

def identify_glyph_type(glyph, width, height):
    """
    Identifies the type of glyph to determine the best stroke width measurement method.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        width: The width of the glyph's bounding box.
        height: The height of the glyph's bounding box.
        
    Returns:
        str: The type of glyph ("vertical_stroke", "horizontal_stroke", "circular", "complex").
    """
    # Check for vertical strokes (tall and narrow)
    if width < height * 0.4 and glyph.numberOfContours == 1:
        return "vertical_stroke"
    
    # Check for horizontal strokes (wide and short)
    if height < width * 0.4 and glyph.numberOfContours == 1:
        return "horizontal_stroke"
    
    # Check for circular glyphs (aspect ratio close to 1, typically 2 contours)
    aspect_ratio = width / height if height > 0 else 0
    if 0.8 < aspect_ratio < 1.2 and glyph.numberOfContours == 2:
        return "circular"
    
    # Complex glyphs (multiple contours or irregular shapes)
    if glyph.numberOfContours > 2 or len(glyph.coordinates) > 30:
        return "complex"
    
    # Default case
    return "complex"

def measure_vertical_stroke_width(glyph, width, height):
    """
    Measures the stroke width of a vertical stroke glyph like 'I' or 'l'.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        width: The width of the glyph's bounding box.
        height: The height of the glyph's bounding box.
        
    Returns:
        float: The estimated stroke width.
    """
    # For vertical strokes, the width is a good approximation of stroke width
    # Sample at multiple heights for better accuracy
    
    # Simple case: use the overall width
    if height > width * 5:  # Very tall and narrow
        return width
    
    # More complex case: sample at different heights
    # This is a simplified approach - a more accurate method would analyze
    # the actual contour at different y-coordinates
    return width * 0.85  # Apply a correction factor

def measure_horizontal_stroke_width(glyph, width, height):
    """
    Measures the stroke width of a horizontal stroke glyph like 'E' or '_'.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        width: The width of the glyph's bounding box.
        height: The height of the glyph's bounding box.
        
    Returns:
        float: The estimated stroke width.
    """
    # For horizontal strokes, the height is a good approximation of stroke width
    return height * 0.85  # Apply a correction factor

def measure_circular_glyph_stroke_width(glyph, coordinates, flags):
    """
    Measures the stroke width of a circular glyph with inner and outer contours like 'O' or 'o'.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        coordinates: The coordinates of the glyph's points.
        flags: The flags of the glyph's points.
        
    Returns:
        float: The estimated stroke width.
    """
    # For circular glyphs with inner and outer contours,
    # we need to identify the inner and outer contours
    
    # Get the endpoints of each contour
    if not hasattr(glyph, 'endPtsOfContours'):
        return None
        
    end_points = glyph.endPtsOfContours
    
    if len(end_points) < 2:
        return None
    
    # Identify the inner and outer contours
    # Typically, the outer contour has more points
    contour1_points = end_points[0] + 1
    contour2_points = end_points[1] - end_points[0]
    
    # Determine which is the outer contour (usually has more points)
    if contour1_points >= contour2_points:
        outer_start, outer_end = 0, end_points[0]
        inner_start, inner_end = end_points[0] + 1, end_points[1]
    else:
        inner_start, inner_end = 0, end_points[0]
        outer_start, outer_end = end_points[0] + 1, end_points[1]
    
    # Calculate the average radius of each contour
    outer_x_coords = [coordinates[i][0] for i in range(outer_start, outer_end + 1)]
    outer_y_coords = [coordinates[i][1] for i in range(outer_start, outer_end + 1)]
    
    inner_x_coords = [coordinates[i][0] for i in range(inner_start, inner_end + 1)]
    inner_y_coords = [coordinates[i][1] for i in range(inner_start, inner_end + 1)]
    
    if not outer_x_coords or not inner_x_coords:
        return None
    
    # Calculate the center of each contour
    outer_center_x = sum(outer_x_coords) / len(outer_x_coords)
    outer_center_y = sum(outer_y_coords) / len(outer_y_coords)
    
    inner_center_x = sum(inner_x_coords) / len(inner_x_coords)
    inner_center_y = sum(inner_y_coords) / len(inner_y_coords)
    
    # Calculate the average radius of each contour
    outer_radius = sum(((x - outer_center_x)**2 + (y - outer_center_y)**2)**0.5 
                      for x, y in zip(outer_x_coords, outer_y_coords)) / len(outer_x_coords)
    
    inner_radius = sum(((x - inner_center_x)**2 + (y - inner_center_y)**2)**0.5 
                      for x, y in zip(inner_x_coords, inner_y_coords)) / len(inner_x_coords)
    
    # The stroke width is the difference between the outer and inner radii
    return outer_radius - inner_radius

def measure_complex_glyph_stroke_width(glyph, coordinates, flags):
    """
    Measures the stroke width of a complex glyph using contour analysis.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        coordinates: The coordinates of the glyph's points.
        flags: The flags of the glyph's points.
        
    Returns:
        float: The estimated stroke width.
    """
    # For complex glyphs, we'll use a combination of methods
    
    # 1. Identify on-curve points
    on_curve_indices = [i for i, flag in enumerate(flags) if flag & 1]
    
    if len(on_curve_indices) < 4:
        return measure_area_perimeter_stroke_width(glyph, None, None)
    
    # 2. Find parallel segments that might represent opposite sides of a stroke
    stroke_widths = []
    
    # Sample a subset of points to reduce computation
    sample_size = min(20, len(on_curve_indices))
    sampled_indices = on_curve_indices[:sample_size]
    
    # For each pair of points, find the closest point on another segment
    for i, idx1 in enumerate(sampled_indices):
        p1 = coordinates[idx1]
        
        # Find the closest point that's not adjacent
        min_dist = float('inf')
        for j, idx2 in enumerate(sampled_indices):
            # Skip adjacent points and self
            if abs(i - j) < 2 or i == j:
                continue
                
            p2 = coordinates[idx2]
            dist = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
            
            if dist < min_dist:
                min_dist = dist
        
        if min_dist < float('inf'):
            stroke_widths.append(min_dist)
    
    # Filter out outliers (values that are too large or too small)
    if stroke_widths:
        stroke_widths.sort()
        # Use the median or lower quartile to avoid outliers
        if len(stroke_widths) >= 3:
            return stroke_widths[len(stroke_widths) // 4]
        else:
            return stroke_widths[0]
    
    # Fallback to area-perimeter method
    return measure_area_perimeter_stroke_width(glyph, None, None)

def measure_area_perimeter_stroke_width(glyph, width=None, height=None):
    """
    Measures the stroke width using an improved area-to-perimeter ratio method.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
        width: The width of the glyph's bounding box (optional).
        height: The height of the glyph's bounding box (optional).
        
    Returns:
        float: The estimated stroke width.
    """
    # If width and height are not provided, calculate them
    if width is None or height is None:
        if not hasattr(glyph, 'coordinates') or len(glyph.coordinates) == 0:
            return None
            
        x_coords = [coord[0] for coord in glyph.coordinates]
        y_coords = [coord[1] for coord in glyph.coordinates]
        
        if not x_coords or not y_coords:
            return None
            
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
    
    # Calculate a more accurate area using the shoelace formula
    # This is a simplified version - for a full implementation,
    # we would need to handle the contours properly
    area = width * height
    
    # Calculate a more accurate perimeter
    # For a more accurate calculation, we would sum the distances
    # between consecutive points along each contour
    perimeter = 2 * (width + height)
    
    # Apply the formula for stroke width
    # For a rectangular stroke, stroke_width ≈ 2 * area / perimeter
    if perimeter > 0:
        # Apply a correction factor based on the glyph's complexity and aspect ratio
        aspect_ratio = width / height if height > 0 else 1
        
        # Adjust correction factor based on aspect ratio and contour count
        if aspect_ratio > 2 or aspect_ratio < 0.5:
            # Very wide or very tall glyphs need a different correction
            correction = 0.4 if glyph.numberOfContours > 1 else 0.2
        else:
            # More balanced glyphs
            correction = 0.6 if glyph.numberOfContours > 1 else 0.3
            
        return (2 * area / perimeter) * correction
    
    return None

def analyze_font_personality(font_info):
    """
    Analyzes the emotional and personality characteristics of a font based on its properties.
    
    Args:
        font_info: A dictionary containing font properties from extract_font_properties.
    
    Returns:
        dict: Information about the font's emotional characteristics and suitable use cases.
    """
    try:
        # Extract relevant properties
        style = font_info['style']
        weight_class = font_info['weight']['class']
        weight_by_stroke = font_info['weight']['weight_by_stroke']
        width_desc = font_info['width']['description']
        shape_type = font_info['shape']['type']
        spacing_width = font_info['spacing']['width_type']
        spacing_type = font_info['spacing']['spacing_type']
        
        # Get new properties if available
        vertical_metrics = font_info.get('vertical_metrics', {})
        contrast_info = font_info.get('contrast', {})
        
        # Initialize personality traits
        personality = {
            'formality': 0,  # -2 (very casual) to 2 (very formal)
            'friendliness': 0,  # -2 (unfriendly) to 2 (very friendly)
            'strength': 0,  # -2 (very weak) to 2 (very strong)
            'elegance': 0,  # -2 (unrefined) to 2 (very elegant)
            'creativity': 0,  # -2 (conventional) to 2 (very creative)
            'modernity': 0,  # -2 (very traditional) to 2 (very modern)
            'playfulness': 0,  # -2 (serious) to 2 (very playful)
            'trustworthiness': 0,  # -2 (untrustworthy) to 2 (very trustworthy)
            'professionalism': 0,  # -2 (unprofessional) to 2 (very professional)
            'warmth': 0,  # -2 (cold) to 2 (very warm)
            'dynamism': 0  # -2 (static) to 2 (very dynamic)
        }
        
        # Analyze style
        if style == "serif":
            personality['formality'] += 1
            personality['elegance'] += 1
            personality['modernity'] -= 1
        elif style == "sans-serif":
            personality['modernity'] += 1
            personality['formality'] += 0.5
        elif style == "script":
            personality['elegance'] += 1.5
            personality['creativity'] += 1.5
            personality['playfulness'] += 1
        elif style == "decorative":
            personality['creativity'] += 2
            personality['playfulness'] += 1.5
            personality['formality'] -= 1
        elif style == "monospace":
            personality['modernity'] += 0.5
            personality['creativity'] -= 1
            
        # Analyze weight
        if weight_by_stroke in ["thin", "light"]:
            personality['elegance'] += 1
            personality['strength'] -= 1
        elif weight_by_stroke in ["medium", "bold"]:
            personality['strength'] += 1
        elif weight_by_stroke in ["extra bold", "black"]:
            personality['strength'] += 2
            personality['formality'] -= 0.5
            
        # Analyze width
        if "condensed" in width_desc.lower():
            personality['modernity'] += 0.5
            personality['elegance'] -= 0.5
        elif "expanded" in width_desc.lower():
            personality['elegance'] += 0.5
            personality['friendliness'] += 0.5
            
        # Analyze shape
        if "curvy" in shape_type:
            personality['friendliness'] += 1
            personality['playfulness'] += 0.5
            if "very" in shape_type:
                personality['friendliness'] += 0.5
                personality['playfulness'] += 0.5
        elif "angular" in shape_type:
            personality['strength'] += 1
            personality['formality'] += 0.5
            
        # Analyze spacing
        if spacing_type == "tight":
            personality['modernity'] += 0.5
        elif spacing_type == "loose":
            personality['friendliness'] += 0.5
            personality['elegance'] += 0.5
            
        # Analyze x-height (new)
        if 'x_height_class' in vertical_metrics:
            x_height_class = vertical_metrics['x_height_class']
            if x_height_class == 'large':
                personality['friendliness'] += 0.5
                personality['modernity'] += 0.5
            elif x_height_class == 'small':
                personality['elegance'] += 0.5
                personality['formality'] += 0.5
                
        # Analyze ascender/descender proportions (new)
        if 'ascender_ratio' in vertical_metrics and 'descender_ratio' in vertical_metrics:
            ascender_ratio = vertical_metrics['ascender_ratio']
            descender_ratio = vertical_metrics['descender_ratio']
            
            # Tall ascenders often convey elegance and formality
            if ascender_ratio > 0.7:
                personality['elegance'] += 0.5
                personality['formality'] += 0.5
                
            # Deep descenders can add creativity and expressiveness
            if descender_ratio > 0.3:
                personality['creativity'] += 0.5
                
        # Analyze contrast (new)
        if 'contrast_type' in contrast_info:
            contrast_type = contrast_info['contrast_type']
            
            if contrast_type in ["high contrast", "extreme contrast"]:
                personality['elegance'] += 1
                personality['formality'] += 0.5
                personality['modernity'] -= 0.5
            elif contrast_type == "monoline":
                personality['modernity'] += 1
                personality['friendliness'] += 0.5
                
        # Normalize personality traits to range -2 to 2
        for trait in personality:
            personality[trait] = max(-2, min(2, personality[trait]))
            
        # Generate emotional description
        description = generate_emotional_description(personality)
        
        # Get dominant traits (top 3 with values > 0)
        traits = [(trait, value) for trait, value in personality.items() if value > 0]
        traits.sort(key=lambda x: x[1], reverse=True)
        dominant_traits = traits[:3]
        
        # Determine suitable use cases
        use_cases = determine_suitable_use_cases(font_info, personality)
        
        return {
            'traits': personality,
            'emotional_description': description,
            'dominant_traits': dominant_traits,
            'suitable_use_cases': use_cases
        }
    except Exception as e:
        print(f"Error analyzing font personality: {e}")
        return {
            'traits': {},
            'emotional_description': "Could not analyze personality",
            'dominant_traits': [],
            'suitable_use_cases': {'suitable_for': [], 'less_suitable_for': []}
        }

def generate_emotional_description(personality):
    """
    Generates a textual description of the font's emotional characteristics.
    
    Args:
        personality: Dictionary of personality trait scores.
    
    Returns:
        str: A textual description of the font's emotional characteristics.
    """
    descriptions = []
    
    # Add descriptions based on personality traits
    for trait, value in personality.items():
        if trait == 'formality':
            if value > 1:
                descriptions.append("projects considerable formality and seriousness")
            elif value > 0:
                descriptions.append("has a somewhat formal character")
            elif value < -1:
                descriptions.append("has a very casual and informal character")
            elif value < 0:
                descriptions.append("has a relaxed, casual feel")
                
        elif trait == 'friendliness':
            if value > 1:
                descriptions.append("has a welcoming and approachable quality")
            elif value > 0:
                descriptions.append("appears friendly and accessible")
            elif value < -1:
                descriptions.append("may appear somewhat cold or distant")
            elif value < 0:
                descriptions.append("has a slightly reserved quality")
                
        elif trait == 'strength':
            if value > 1:
                descriptions.append("projects considerable strength and confidence")
            elif value > 0:
                descriptions.append("conveys stability and assurance")
            elif value < -1:
                descriptions.append("appears delicate and light")
            elif value < 0:
                descriptions.append("has a somewhat gentle character")
                
        elif trait == 'elegance':
            if value > 1:
                descriptions.append("exudes sophistication and elegance")
            elif value > 0:
                descriptions.append("has a refined, polished quality")
            elif value < -1:
                descriptions.append("has a deliberately unrefined, raw quality")
            elif value < 0:
                descriptions.append("prioritizes function over aesthetic refinement")
                
        elif trait == 'creativity':
            if value > 1:
                descriptions.append("is highly creative and expressive")
            elif value > 0:
                descriptions.append("shows creative character")
            elif value < -1:
                descriptions.append("is very conventional and practical")
            elif value < 0:
                descriptions.append("has a straightforward, no-nonsense quality")
                
        elif trait == 'modernity':
            if value > 1:
                descriptions.append("has a very contemporary, modern aesthetic")
            elif value > 0:
                descriptions.append("feels current and up-to-date")
            elif value < -1:
                descriptions.append("has a distinctly traditional or classical feel")
            elif value < 0:
                descriptions.append("has somewhat traditional characteristics")
                
        elif trait == 'playfulness':
            if value > 1:
                descriptions.append("is playful and fun")
            elif value > 0:
                descriptions.append("has a touch of playfulness")
            elif value < -1:
                descriptions.append("is very serious and businesslike")
            elif value < 0:
                descriptions.append("maintains a certain seriousness")
        
        elif trait == 'trustworthiness':
            if value > 1:
                descriptions.append("conveys a strong sense of trust and reliability")
            elif value > 0:
                descriptions.append("appears trustworthy and dependable")
            elif value < -1:
                descriptions.append("may appear untrustworthy or deceptive")
            elif value < 0:
                descriptions.append("has a slightly untrustworthy quality")
                
        elif trait == 'professionalism':
            if value > 1:
                descriptions.append("exudes professionalism and competence")
            elif value > 0:
                descriptions.append("appears professional and polished")
            elif value < -1:
                descriptions.append("may appear unprofessional or amateurish")
            elif value < 0:
                descriptions.append("has a slightly unprofessional quality")
                
        elif trait == 'warmth':
            if value > 1:
                descriptions.append("conveys a warm and inviting atmosphere")
            elif value > 0:
                descriptions.append("appears warm and friendly")
            elif value < -1:
                descriptions.append("may appear cold or distant")
            elif value < 0:
                descriptions.append("has a slightly cold quality")
                
        elif trait == 'dynamism':
            if value > 1:
                descriptions.append("conveys energy and movement")
            elif value > 0:
                descriptions.append("appears dynamic and lively")
            elif value < -1:
                descriptions.append("may appear static or unchanging")
            elif value < 0:
                descriptions.append("has a slightly static quality")
    
    # Filter out None values and empty strings
    descriptions = [d for d in descriptions if d]
    
    # Combine descriptions into a coherent paragraph
    if descriptions:
        if len(descriptions) == 1:
            return f"This font {descriptions[0]}."
        elif len(descriptions) == 2:
            return f"This font {descriptions[0]} and {descriptions[1]}."
        else:
            combined = ", ".join(descriptions[:-1]) + f", and {descriptions[-1]}"
            return f"This font {combined}."
    
    return "This font has a balanced personality without strongly pronounced characteristics."

def determine_suitable_use_cases(font_info, personality):
    """
    Determines suitable use cases for the font based on its personality traits.
    
    Args:
        font_info: A dictionary containing font properties from extract_font_properties.
        personality: Dictionary of personality trait scores.
    
    Returns:
        dict: Dictionary with lists of suitable and less suitable use cases.
    """
    # Extract style and weight information
    style = font_info['style']
    weight_by_stroke = font_info['weight']['weight_by_stroke']
    
    use_cases = {
        'suitable_for': [],
        'less_suitable_for': []
    }
    
    # Determine suitable use cases based on personality traits
    if personality['formality'] > 1 and personality['elegance'] > 0:
        use_cases['suitable_for'].extend([
            "Formal invitations",
            "Luxury branding",
            "High-end restaurant menus",
            "Wedding stationery"
        ])
    
    if personality['formality'] > 0 and personality['modernity'] > 0:
        use_cases['suitable_for'].extend([
            "Corporate communications",
            "Business websites",
            "Professional reports",
            "Legal documents"
        ])
    
    if personality['friendliness'] > 1 and personality['playfulness'] > 0:
        use_cases['suitable_for'].extend([
            "Children's books",
            "Casual brand messaging",
            "Greeting cards",
            "Informal invitations"
        ])
    
    if personality['creativity'] > 1 and personality['playfulness'] > 0:
        use_cases['suitable_for'].extend([
            "Creative agency branding",
            "Art exhibition materials",
            "Entertainment industry",
            "Festival promotions"
        ])
    
    if personality['modernity'] > 1 and personality['strength'] > 0:
        use_cases['suitable_for'].extend([
            "Tech company branding",
            "Sports marketing",
            "Modern advertising",
            "App interfaces"
        ])
    
    if personality['elegance'] > 1 and personality['creativity'] > 0:
        use_cases['suitable_for'].extend([
            "Fashion branding",
            "Beauty product packaging",
            "Lifestyle magazines",
            "Boutique marketing"
        ])
    
    # Determine less suitable use cases
    if personality['formality'] > 1 and personality['elegance'] > 1:
        use_cases['less_suitable_for'].extend([
            "Casual social media posts",
            "Children's content",
            "Playful advertising"
        ])
    
    if personality['playfulness'] > 1 and personality['creativity'] > 1:
        use_cases['less_suitable_for'].extend([
            "Legal documents",
            "Academic papers",
            "Medical information",
            "Financial reports"
        ])
    
    if personality['modernity'] < -1 and personality['creativity'] < -1:
        use_cases['less_suitable_for'].extend([
            "Tech startups",
            "Modern digital interfaces",
            "Youth-oriented brands"
        ])
    
    # Add style-specific use cases
    if style == "serif" and weight_by_stroke in ["regular", "medium"]:
        use_cases['suitable_for'].extend([
            "Long-form reading",
            "Book typography",
            "News publications"
        ])
    
    if style == "sans-serif" and weight_by_stroke in ["regular", "medium"]:
        use_cases['suitable_for'].extend([
            "User interfaces",
            "Signage",
            "Information design"
        ])
    
    if style == "script":
        use_cases['suitable_for'].extend([
            "Wedding invitations",
            "Certificates",
            "Greeting cards"
        ])
        use_cases['less_suitable_for'].extend([
            "Long paragraphs of text",
            "Small size applications",
            "Technical documentation"
        ])
    
    if style == "decorative":
        use_cases['suitable_for'].extend([
            "Headlines",
            "Logo design",
            "Short display text"
        ])
        use_cases['less_suitable_for'].extend([
            "Body text",
            "Long-form content",
            "Small size applications"
        ])
    
    # Remove duplicates
    use_cases['suitable_for'] = list(set(use_cases['suitable_for']))
    use_cases['less_suitable_for'] = list(set(use_cases['less_suitable_for']))
    
    return use_cases

def classify_font_width_by_aspect_ratio(font):
    """
    Measures the width of characters relative to their height and classifies the font.
    
    Args:
        font: A TTFont object.
    
    Returns:
        dict: Information about the font's width classification based on aspect ratios.
    """
    try:
        # Check if the font has a 'glyf' table (TrueType outlines)
        if 'glyf' not in font:
            return {
                'aspect_ratio': None,
                'width_by_aspect': 'unknown',
                'reason': 'No glyf table (possibly CFF/OTF)'
            }
        
        # Get the cmap to map Unicode values to glyph names
        cmap = font.getBestCmap()
        if not cmap:
            return {
                'aspect_ratio': None,
                'width_by_aspect': 'unknown',
                'reason': 'No cmap table found'
            }
        
        # Sample glyphs for width analysis
        # We'll use characters with distinctive width characteristics
        sample_chars = ['m', 'w', 'o', 'H', 'O']
        sample_unicodes = [ord(char) for char in sample_chars]
        
        # Get glyph names for these characters
        glyph_names = [cmap.get(unicode_val) for unicode_val in sample_unicodes if unicode_val in cmap]
        
        if not glyph_names:
            return {
                'aspect_ratio': None,
                'width_by_aspect': 'unknown',
                'reason': 'No sample glyphs found'
            }
        
        # Collect aspect ratios
        aspect_ratios = []
        
        for glyph_name in glyph_names:
            if not glyph_name or glyph_name not in font['glyf']:
                continue
                
            glyph = font['glyf'][glyph_name]
            
            # Skip empty glyphs
            if glyph.numberOfContours <= 0:
                continue
            
            # Measure aspect ratio for this glyph
            aspect_ratio = measure_glyph_aspect_ratio(glyph)
            if aspect_ratio is not None and aspect_ratio > 0:
                aspect_ratios.append(aspect_ratio)
        
        if not aspect_ratios:
            return {
                'aspect_ratio': None,
                'width_by_aspect': 'unknown',
                'reason': 'Could not measure aspect ratios'
            }
        
        # Calculate average aspect ratio
        average_aspect_ratio = sum(aspect_ratios) / len(aspect_ratios)
        
        # Classify width based on average aspect ratio
        # These thresholds can be adjusted based on testing with various fonts
        if average_aspect_ratio < 0.7:
            width_class = "condensed"
        elif average_aspect_ratio < 1.0:
            width_class = "normal"
        else:
            width_class = "expanded"
        
        return {
            'aspect_ratio': average_aspect_ratio,
            'width_by_aspect': width_class
        }
        
    except Exception as e:
        return {
            'aspect_ratio': None,
            'width_by_aspect': 'error',
            'reason': str(e)
        }

def measure_glyph_aspect_ratio(glyph):
    """
    Measures the aspect ratio (width/height) of a glyph.
    
    Args:
        glyph: A glyph object from the 'glyf' table.
    
    Returns:
        float: The aspect ratio of the glyph, or None if it couldn't be measured.
    """
    try:
        # Check if the glyph has coordinates
        if not hasattr(glyph, 'coordinates') or len(glyph.coordinates) == 0:
            return None
        
        # Get the bounding box of the glyph
        x_coords = [coord[0] for coord in glyph.coordinates]
        y_coords = [coord[1] for coord in glyph.coordinates]
        
        if not x_coords or not y_coords:
            return None
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Calculate width and height
        width = x_max - x_min
        height = y_max - y_min
        
        # Avoid division by zero
        if height <= 0:
            return None
        
        # Calculate aspect ratio (width/height)
        return width / height
        
    except Exception as e:
        print(f"Error measuring glyph aspect ratio: {e}")
        return None

def analyze_vertical_metrics(font):
    """
    Analyzes the vertical metrics of a font including x-height, cap height, and ascender/descender proportions.
    
    Args:
        font: A TTFont object.
        
    Returns:
        dict: Information about the font's vertical metrics.
    """
    try:
        # Check if the font has the necessary tables
        if 'glyf' not in font or 'head' not in font or 'hhea' not in font or 'OS/2' not in font:
            return {
                'error': 'Missing required tables for vertical metrics analysis'
            }
        
        # Get units per em from the head table for normalization
        units_per_em = font['head'].unitsPerEm
        
        # Get metrics from OS/2 table if available (more reliable)
        os2 = font['OS/2']
        metrics = {}
        
        # Get x-height from OS/2 table (if available)
        if hasattr(os2, 'sxHeight') and os2.sxHeight > 0:
            metrics['x_height'] = os2.sxHeight
            metrics['normalized_x_height'] = os2.sxHeight / units_per_em
        else:
            # Fallback: measure x-height from 'x' glyph
            x_height = measure_glyph_height(font, 'x')
            if x_height:
                metrics['x_height'] = x_height
                metrics['normalized_x_height'] = x_height / units_per_em
        
        # Get cap height from OS/2 table (if available)
        if hasattr(os2, 'sCapHeight') and os2.sCapHeight > 0:
            metrics['cap_height'] = os2.sCapHeight
            metrics['normalized_cap_height'] = os2.sCapHeight / units_per_em
        else:
            # Fallback: measure cap height from 'H' glyph
            cap_height = measure_glyph_height(font, 'H')
            if cap_height:
                metrics['cap_height'] = cap_height
                metrics['normalized_cap_height'] = cap_height / units_per_em
        
        # Get ascender and descender values
        # Try OS/2 table first (typographic ascender/descender)
        if hasattr(os2, 'sTypoAscender') and hasattr(os2, 'sTypoDescender'):
            metrics['ascender'] = os2.sTypoAscender
            metrics['descender'] = os2.sTypoDescender
        # Fallback to hhea table
        elif hasattr(font['hhea'], 'ascent') and hasattr(font['hhea'], 'descent'):
            metrics['ascender'] = font['hhea'].ascent
            metrics['descender'] = font['hhea'].descent
        
        # Calculate normalized values
        if 'ascender' in metrics and 'descender' in metrics:
            metrics['normalized_ascender'] = metrics['ascender'] / units_per_em
            metrics['normalized_descender'] = abs(metrics['descender']) / units_per_em
            
            # Calculate total height (ascender to descender)
            metrics['total_height'] = metrics['ascender'] - metrics['descender']
            metrics['normalized_total_height'] = metrics['total_height'] / units_per_em
            
            # Calculate ascender-to-height and descender-to-height ratios
            metrics['ascender_ratio'] = metrics['ascender'] / metrics['total_height']
            metrics['descender_ratio'] = abs(metrics['descender']) / metrics['total_height']
        
        # Calculate x-height to cap-height ratio (if both are available)
        if 'x_height' in metrics and 'cap_height' in metrics and metrics['cap_height'] > 0:
            metrics['x_to_cap_ratio'] = metrics['x_height'] / metrics['cap_height']
            
            # Classify the x-height
            if metrics['x_to_cap_ratio'] < 0.65:
                metrics['x_height_class'] = 'small'
            elif metrics['x_to_cap_ratio'] < 0.75:
                metrics['x_height_class'] = 'medium'
            else:
                metrics['x_height_class'] = 'large'
        
        return metrics
        
    except Exception as e:
        return {'error': f'Error analyzing vertical metrics: {str(e)}'}

def measure_glyph_height(font, char):
    """
    Measures the height of a specific glyph.
    
    Args:
        font: A TTFont object.
        char: The character to measure.
        
    Returns:
        float: The height of the glyph, or None if it couldn't be measured.
    """
    try:
        # Get the glyph name for the character
        cmap = font.getBestCmap()
        if ord(char) not in cmap:
            return None
            
        glyph_name = cmap[ord(char)]
        glyph = font['glyf'][glyph_name]
        
        # Check if the glyph has coordinates
        if not hasattr(glyph, 'coordinates') or len(glyph.coordinates) == 0:
            return None
        
        # Get y coordinates
        y_coords = [coord[1] for coord in glyph.coordinates]
        
        if not y_coords:
            return None
        
        # Calculate height
        y_min, y_max = min(y_coords), max(y_coords)
        height = y_max - y_min
        
        return height
        
    except Exception:
        return None

def analyze_stroke_contrast(font):
    """
    Analyzes the contrast (variation in stroke thickness) of a font.
    
    Args:
        font: A TTFont object.
        
    Returns:
        dict: Information about the font's stroke contrast.
    """
    try:
        # Check if the font has a glyf table
        if 'glyf' not in font:
            return {'contrast_ratio': None, 'contrast_type': 'unknown', 'reason': 'No glyf table'}
        
        # Sample characters that typically show contrast
        sample_chars = ['O', 'o', 'B', 'b', 'D', 'd']
        
        # Get the glyph names for these characters
        cmap = font.getBestCmap()
        glyph_names = []
        for char in sample_chars:
            if ord(char) in cmap:
                glyph_names.append(cmap[ord(char)])
        
        if not glyph_names:
            return {'contrast_ratio': None, 'contrast_type': 'unknown', 'reason': 'No sample glyphs found'}
        
        # Simplified approach: measure stroke width at different angles
        # and calculate the ratio between max and min
        contrast_ratios = []
        
        for glyph_name in glyph_names:
            if not glyph_name or glyph_name not in font['glyf']:
                continue
                
            glyph = font['glyf'][glyph_name]
            
            # Skip empty glyphs
            if glyph.numberOfContours <= 0:
                continue
            
            # Get the glyph's bounding box
            if hasattr(glyph, 'xMin') and hasattr(glyph, 'xMax') and hasattr(glyph, 'yMin') and hasattr(glyph, 'yMax'):
                width = glyph.xMax - glyph.xMin
                height = glyph.yMax - glyph.yMin
                
                # Skip glyphs that are too small
                if width <= 0 or height <= 0:
                    continue
                
                # For circular glyphs like 'O', 'o'
                if glyph_name in [cmap.get(ord('O')), cmap.get(ord('o'))]:
                    # Estimate horizontal and vertical stroke widths using the bounding box
                    # This is a simplified approach
                    if glyph.numberOfContours >= 2:
                        # For a typical 'O', the outer contour is larger than the inner
                        # We can estimate the stroke width as a percentage of the total width/height
                        horizontal_width = width * 0.15  # Approximate
                        vertical_width = height * 0.15   # Approximate
                        
                        if horizontal_width > 0 and vertical_width > 0:
                            ratio = max(horizontal_width, vertical_width) / min(horizontal_width, vertical_width)
                            contrast_ratios.append(ratio)
                
                # For other characters like 'B', 'D'
                elif glyph_name in [cmap.get(ord('B')), cmap.get(ord('D')), cmap.get(ord('b')), cmap.get(ord('d'))]:
                    # These characters typically have thicker vertical strokes than horizontal
                    # We can estimate based on the aspect ratio
                    if width > 0 and height > 0:
                        aspect_ratio = width / height
                        
                        # Estimate stroke widths
                        vertical_width = width * 0.2   # Vertical stroke is about 20% of width
                        horizontal_width = height * 0.1  # Horizontal stroke is about 10% of height
                        
                        if horizontal_width > 0 and vertical_width > 0:
                            ratio = max(horizontal_width, vertical_width) / min(horizontal_width, vertical_width)
                            contrast_ratios.append(ratio)
        
        # If we have contrast ratios, calculate the average
        if contrast_ratios:
            avg_contrast_ratio = sum(contrast_ratios) / len(contrast_ratios)
            
            # Classify contrast
            if avg_contrast_ratio < 1.1:
                contrast_type = "monoline"
            elif avg_contrast_ratio < 1.5:
                contrast_type = "low contrast"
            elif avg_contrast_ratio < 2.5:
                contrast_type = "medium contrast"
            elif avg_contrast_ratio < 4.0:
                contrast_type = "extreme contrast"
                
            return {
                'contrast_ratio': avg_contrast_ratio,
                'contrast_type': contrast_type,
                'sample_size': len(contrast_ratios)
            }
        
        # Fallback: use style to estimate contrast
        style = determine_font_style(font)
        if style == "serif":
            # Serif fonts typically have medium to high contrast
            return {
                'contrast_ratio': 2.5,
                'contrast_type': "medium contrast",
                'estimated': True
            }
        elif style == "sans-serif":
            # Sans-serif fonts typically have low contrast
            return {
                'contrast_ratio': 1.2,
                'contrast_type': "low contrast",
                'estimated': True
            }
        elif style == "script":
            # Script fonts can have medium to high contrast
            return {
                'contrast_ratio': 2.0,
                'contrast_type': "medium contrast",
                'estimated': True
            }
        else:
            # Default fallback
            return {
                'contrast_ratio': 1.5,
                'contrast_type': "low contrast",
                'estimated': True
            }
            
    except Exception as e:
        print(f"Error in analyze_stroke_contrast: {e}")
        return {'contrast_ratio': None, 'contrast_type': 'error', 'reason': str(e)}

def detect_font_format(font, font_path):
    """
    Detects the format of a font file based on file extension and font tables.
    
    Args:
        font: A TTFont object.
        font_path (str): Path to the font file.
    
    Returns:
        str: The detected font format ('TrueType', 'OpenType-CFF', 'OpenType-TT', 'WOFF', 'WOFF2').
    """
    # Check file extension first
    ext = os.path.splitext(font_path)[1].lower()
    
    # Check for WOFF and WOFF2 formats
    if ext == '.woff2':
        return 'WOFF2'
    elif ext == '.woff':
        return 'WOFF'
    
    # Check for OpenType vs TrueType
    if 'CFF ' in font or 'CFF2' in font:
        # OpenType with CFF outlines (PostScript-based)
        if ext == '.otf':
            return 'OpenType-CFF'
        else:
            return 'OpenType-CFF'
    elif 'glyf' in font:
        # TrueType outlines
        if ext == '.otf':
            return 'OpenType-TT'
        else:
            return 'TrueType'
    
    # Fallback based on extension
    if ext == '.otf':
        return 'OpenType'
    elif ext == '.ttf':
        return 'TrueType'
    
    # If we can't determine, return a generic response
    return 'Unknown'

def extract_font_properties(font_path):
    """
    Loads a font file and extracts its style, weight, width, shape, and spacing.
    Supports TrueType (.ttf), OpenType (.otf), WOFF, and WOFF2 formats.
    
    Args:
        font_path (str): Path to the font file.
    
    Returns:
        dict: Font properties including style, weight, width, shape, and spacing.
    """
    try:
        # Load the font file
        font = TTFont(font_path)
        
        # Detect font format
        font_format = detect_font_format(font, font_path)
        
        # Extract weight from OS/2 table (e.g., 400 = normal, 700 = bold)
        # OS/2 table contains usWeightClass which is a numeric value representing weight
        weight_class = font['OS/2'].usWeightClass
        
        # Map weight class to descriptive terms
        weight_map = {
            100: "Thin",
            200: "Extra Light",
            300: "Light",
            400: "Regular",
            500: "Medium",
            600: "Semi Bold",
            700: "Bold",
            800: "Extra Bold",
            900: "Black"
        }
        weight_desc = weight_map.get(weight_class, "Custom")
        
        # Calculate stroke width and get weight classification based on it
        stroke_info = calculate_stroke_width(font)
        
        # Extract width from OS/2 table (e.g., 5 = normal, 3 = condensed)
        # usWidthClass ranges from 1 (ultra-condensed) to 9 (ultra-expanded)
        width_class = font['OS/2'].usWidthClass
        
        # Map width class to descriptive terms
        width_map = {
            1: "Ultra Condensed",
            2: "Extra Condensed",
            3: "Condensed",
            4: "Semi Condensed",
            5: "Normal",
            6: "Semi Expanded",
            7: "Expanded",
            8: "Extra Expanded",
            9: "Ultra Expanded"
        }
        width_desc = width_map.get(width_class, "Custom")
        
        # Calculate aspect ratio and get width classification based on it
        aspect_ratio_info = classify_font_width_by_aspect_ratio(font)
        
        # Determine style using the new function
        style = determine_font_style(font)
        
        # Analyze shape (curvy vs. angular) by examining glyph outlines
        shape_info = analyze_glyph_shapes(font)
        
        # Analyze spacing using the horizontal metrics (hmtx) table
        spacing_info = analyze_spacing(font)
        
        # Analyze vertical metrics (x-height, cap height, ascender/descender)
        vertical_metrics = analyze_vertical_metrics(font)
        
        # Analyze stroke contrast
        contrast_info = analyze_stroke_contrast(font)
        
        # Create the font properties dictionary
        font_properties = {
            'format': font_format,
            'style': style,
            'weight': {
                'class': weight_class,
                'description': weight_desc,
                'stroke_width': stroke_info.get('stroke_width'),
                'normalized_stroke_width': stroke_info.get('normalized_stroke_width'),
                'weight_by_stroke': stroke_info.get('weight_by_stroke')
            },
            'width': {
                'class': width_class,
                'description': width_desc,
                'aspect_ratio': aspect_ratio_info.get('aspect_ratio'),
                'width_by_aspect': aspect_ratio_info.get('width_by_aspect')
            },
            'shape': shape_info,
            'spacing': spacing_info,
            'vertical_metrics': vertical_metrics,
            'contrast': contrast_info,
            'font_name': font['name'].getName(4, 3, 1, 1033).toStr() if font['name'].getName(4, 3, 1, 1033) else "Unknown"
        }
        
        # Add personality analysis
        font_properties['personality'] = analyze_font_personality(font_properties)
        
        return font_properties
    except Exception as e:
        print(f"Error loading font: {e}")
        return None

def analyze_glyph_shapes(font):
    """
    Analyzes the shapes of glyphs to determine if they are curvy or angular.
    Supports both TrueType (glyf) and OpenType (CFF) outlines.
    
    Args:
        font: A TTFont object.
        
    Returns:
        dict: Information about the shape characteristics.
    """
    try:
        # Get the cmap to map Unicode values to glyph names
        cmap = font.getBestCmap()
        if not cmap:
            return {'type': 'unknown', 'reason': 'No cmap table found'}
        
        # Sample common characters for analysis
        # Include a mix of typically curved and angular characters
        sample_chars = ['a', 'e', 'o', 'n', 'h', 'm', 'v', 'w', 's', 'c', 'z', 'k']
        sample_unicodes = [ord(char) for char in sample_chars]
        
        # Get the glyph names for these characters
        glyph_names = [cmap.get(unicode_val) for unicode_val in sample_unicodes if unicode_val in cmap]
        
        if not glyph_names:
            return {'type': 'unknown', 'reason': 'No sample glyphs found'}
        
        # For TrueType fonts, analyze glyph outlines
        if 'glyf' in font:
            # Metrics to determine curviness
            curve_segments = 0
            straight_segments = 0
            total_angle_changes = 0
            
            for glyph_name in glyph_names:
                if not glyph_name or glyph_name not in font['glyf']:
                    continue
                    
                glyph = font['glyf'][glyph_name]
                
                # Skip empty glyphs
                if glyph.numberOfContours <= 0:
                    continue
                
                # Get the glyph's coordinates and flags
                if not hasattr(glyph, 'coordinates') or not hasattr(glyph, 'flags'):
                    continue
                    
                coordinates = glyph.coordinates
                flags = glyph.flags
                
                if len(coordinates) != len(flags):
                    continue
                
                # In TrueType, curves are represented by quadratic Bézier curves
                # On-curve points have bit 0 set (flag & 1 == 1)
                # Off-curve points are control points for Bézier curves
                
                # Count on-curve and off-curve points
                on_curve_points = sum(1 for flag in flags if flag & 1)
                off_curve_points = len(flags) - on_curve_points
                
                # More off-curve points indicate more curves
                if on_curve_points > 0:
                    curve_ratio = off_curve_points / on_curve_points
                    curve_segments += off_curve_points
                    straight_segments += on_curve_points
                    
                    # Analyze angle changes between consecutive on-curve points
                    # to detect sharp corners vs. smooth curves
                    on_curve_indices = [i for i, flag in enumerate(flags) if flag & 1]
                    
                    if len(on_curve_indices) >= 3:
                        for i in range(len(on_curve_indices)):
                            idx1 = on_curve_indices[i]
                            idx2 = on_curve_indices[(i + 1) % len(on_curve_indices)]
                            idx3 = on_curve_indices[(i + 2) % len(on_curve_indices)]
                            
                            # Get the coordinates of three consecutive on-curve points
                            p1 = coordinates[idx1]
                            p2 = coordinates[idx2]
                            p3 = coordinates[idx3]
                            
                            # Calculate vectors between points
                            v1 = (p2[0] - p1[0], p2[1] - p1[1])
                            v2 = (p3[0] - p2[0], p3[1] - p2[1])
                            
                            # Skip if any vector has zero length
                            if (v1[0] == 0 and v1[1] == 0) or (v2[0] == 0 and v2[1] == 0):
                                continue
                            
                            # Calculate the angle between vectors using dot product
                            dot_product = v1[0] * v2[0] + v1[1] * v2[1]
                            v1_mag = (v1[0]**2 + v1[1]**2)**0.5
                            v2_mag = (v2[0]**2 + v2[1]**2)**0.5
                            
                            if v1_mag * v2_mag == 0:
                                continue
                                
                            cos_angle = max(-1, min(1, dot_product / (v1_mag * v2_mag)))
                            angle = math.acos(cos_angle)
                            
                            # Convert to degrees
                            angle_deg = angle * 180 / math.pi
                            
                            # Add to total angle changes
                            total_angle_changes += angle_deg
            
            # Calculate metrics
            results = {}
            
            # Curve ratio based on off-curve to on-curve points
            if straight_segments > 0:
                curve_ratio = curve_segments / straight_segments
                results['curve_to_straight_ratio'] = curve_ratio
                
                # Determine shape type based on curve ratio
                if curve_ratio > 1.5:
                    shape_type = "very curvy"
                elif curve_ratio > 1.0:
                    shape_type = "curvy"
                elif curve_ratio > 0.6:
                    shape_type = "moderately curvy"
                elif curve_ratio > 0.3:
                    shape_type = "slightly curvy"
                else:
                    shape_type = "angular"
                    
                results['type'] = shape_type
            else:
                results['type'] = "unknown"
                results['reason'] = "Could not analyze contours"
                
            # Add average angle change if available
            if total_angle_changes > 0 and straight_segments > 0:
                avg_angle_change = total_angle_changes / straight_segments
                results['average_angle_change'] = avg_angle_change
                
                # Adjust shape type based on angle changes
                # Sharp angles (closer to 90 degrees) indicate more angular shapes
                if avg_angle_change > 60 and 'type' in results:
                    # Make the shape more angular if there are sharp angles
                    if results['type'] == "very curvy":
                        results['type'] = "curvy"
                    elif results['type'] == "curvy":
                        results['type'] = "moderately curvy"
                    elif results['type'] == "moderately curvy":
                        results['type'] = "slightly curvy"
                    elif results['type'] == "slightly curvy":
                        results['type'] = "angular"
            
            return results
        
        # For OpenType CFF fonts, use a different approach
        elif 'CFF ' in font or 'CFF2' in font:
            # For CFF fonts, we'll use font metadata to estimate curviness
            # Check font name for indicators
            font_name = ""
            if 'name' in font and font['name'].getName(1, 3, 1, 1033):
                font_name = font['name'].getName(1, 3, 1, 1033).toStr().lower()
            
            # Check for keywords in the font name
            curvy_keywords = ['round', 'soft', 'curv', 'script', 'brush', 'hand']
            angular_keywords = ['angular', 'gothic', 'square', 'geo', 'block', 'pixel']
            
            curvy_score = sum(1 for keyword in curvy_keywords if keyword in font_name)
            angular_score = sum(1 for keyword in angular_keywords if keyword in font_name)
            
            # Check OS/2 table for additional clues
            if 'OS/2' in font and hasattr(font['OS/2'], 'panose'):
                panose = font['OS/2'].panose
                
                # Check panose.bLetterForm (0-15)
                # 2-5 are more angular, 9-11 are more curvy
                if hasattr(panose, 'bLetterForm'):
                    if 2 <= panose.bLetterForm <= 5:
                        angular_score += 2
                    elif 9 <= panose.bLetterForm <= 11:
                        curvy_score += 2
            
            # Determine shape type based on scores
            if curvy_score > angular_score:
                shape_type = "curvy"
            elif angular_score > curvy_score:
                shape_type = "angular"
            else:
                shape_type = "balanced"
            
            return {
                'type': shape_type,
                'is_estimated': True,
                'estimation_method': 'metadata analysis',
                'curvy_score': curvy_score,
                'angular_score': angular_score
            }
            
        else:
            return {'type': 'unknown', 'reason': 'Unsupported font format'}
              
    except Exception as e:
        print(f"Error analyzing glyph shapes: {e}")
        return {'type': 'unknown', 'reason': str(e)}

def analyze_spacing(font):
    """
    Analyzes the spacing characteristics of the font using the hmtx table.
    Supports both TrueType and OpenType fonts.
    
    Args:
        font: A TTFont object.
        
    Returns:
        dict: Information about the spacing characteristics.
    """
    try:
        # All OpenType and TrueType fonts should have an hmtx table
        if 'hmtx' not in font:
            return {
                'width_type': 'unknown',
                'spacing_type': 'unknown',
                'reason': 'No hmtx table'
            }
        
        # Get horizontal metrics
        hmtx = font['hmtx']
        
        # Calculate average advance width and side bearing
        advance_widths = [metrics[0] for metrics in hmtx.metrics.values()]
        left_side_bearings = [metrics[1] for metrics in hmtx.metrics.values()]
        
        if not advance_widths:
            return {
                'width_type': 'unknown',
                'spacing_type': 'unknown',
                'reason': 'No metrics found'
            }
        
        avg_width = sum(advance_widths) / len(advance_widths)
        avg_bearing = sum(left_side_bearings) / len(left_side_bearings) if left_side_bearings else 0
        
        # Get units per em from the head table
        units_per_em = font['head'].unitsPerEm
        
        # Normalize metrics relative to em size
        normalized_width = avg_width / units_per_em
        normalized_bearing = avg_bearing / units_per_em
        
        # Determine spacing type
        if normalized_width > 0.7:
            width_type = "very wide"
        elif normalized_width > 0.6:
            width_type = "wide"
        elif normalized_width > 0.5:
            width_type = "medium"
        elif normalized_width > 0.4:
            width_type = "narrow"
        else:
            width_type = "very narrow"
            
        # Determine bearing/spacing type
        if normalized_bearing > 0.1:
            bearing_type = "loose"
        elif normalized_bearing > 0.05:
            bearing_type = "medium"
        else:
            bearing_type = "tight"
            
        # For CFF fonts, check if there's additional spacing info in the CFF table
        is_cff = 'CFF ' in font or 'CFF2' in font
        
        return {
            'average_width': avg_width,
            'average_bearing': avg_bearing,
            'normalized_width': normalized_width,
            'normalized_bearing': normalized_bearing,
            'width_type': width_type,
            'spacing_type': bearing_type,
            'is_cff': is_cff
        }
        
    except Exception as e:
        print(f"Error analyzing spacing: {e}")
        return {
            'width_type': 'error',
            'spacing_type': 'error',
            'reason': str(e)
        }

# Example usage
if __name__ == "__main__":
    # Test with Roboto (a sans-serif font)
    roboto_info = extract_font_properties("fonts/KFOmCnqEu92Fr1Mu4mxP.ttf")
    if roboto_info:
        print("\nRoboto Font Analysis:")
        print(f"Font Name: {roboto_info['font_name']}")
        print(f"Style: {roboto_info['style']}")
        print(f"Weight: {roboto_info['weight']['description']} ({roboto_info['weight']['class']})")
        print(f"Width: {roboto_info['width']['description']} ({roboto_info['width']['class']})")
        print(f"Shape: {roboto_info['shape']['type']}")
        print(f"Spacing: {roboto_info['spacing']['width_type']} width, {roboto_info['spacing']['spacing_type']} spacing")
    
    # Test with Pacifico (a script font)
    pacifico_info = extract_font_properties("fonts/FwZY7-Qmy14u9lezJ-6H6Mw.ttf")
    if pacifico_info:
        print("\nPacifico Font Analysis:")
        print(f"Font Name: {pacifico_info['font_name']}")
        print(f"Style: {pacifico_info['style']}")
        print(f"Weight: {pacifico_info['weight']['description']} ({pacifico_info['weight']['class']})")
        print(f"Width: {pacifico_info['width']['description']} ({pacifico_info['width']['class']})")
        print(f"Shape: {pacifico_info['shape']['type']}")
        print(f"Spacing: {pacifico_info['spacing']['width_type']} width, {pacifico_info['spacing']['spacing_type']} spacing")

def visualize_font_properties(font_info, output_dir=None):
    """
    Create visualizations of font properties and analysis results.
    
    Args:
        font_info (dict): Dictionary containing font analysis results
        output_dir (str, optional): Directory to save visualizations. If None, displays them instead.
        
    Returns:
        dict: Paths to generated visualization files if output_dir is provided, otherwise None
    """
    # Set the backend to 'Agg' which is non-interactive and doesn't require a GUI
    import matplotlib
    matplotlib.use('Agg')
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    import os
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib.patches import Patch
    from io import BytesIO
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Create output directory if needed
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Dictionary to store paths to visualization files
    visualization_paths = {}
    
    # 1. Create personality radar chart
    if 'personality' in font_info and 'dominant_traits' in font_info['personality']:
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
        
        # Extract traits and values
        traits = [t[0].capitalize() for t in font_info['personality']['dominant_traits']]
        values = [t[1] for t in font_info['personality']['dominant_traits']]
        
        # Number of variables
        N = len(traits)
        
        # Compute angle for each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Add values (and close the loop)
        values += values[:1]
        
        # Draw the plot
        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.25)
        
        # Set labels and title
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(traits)
        ax.set_title(f"Font Personality Profile: {font_info['font_name']}", size=15, pad=20)
        
        # Adjust radial limits
        ax.set_ylim(0, 10)
        
        # Save or display
        if output_dir:
            radar_path = os.path.join(output_dir, f"{font_info['font_name'].replace(' ', '_')}_personality_radar.png")
            plt.savefig(radar_path, dpi=300, bbox_inches='tight')
            visualization_paths['personality_radar'] = radar_path
            plt.close(fig)
        else:
            plt.tight_layout()
            plt.show()
    
    # 2. Create weight and width comparison chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define standard weights and widths for comparison
    standard_weights = {
        'thin': 100, 
        'extra light': 200, 
        'light': 300, 
        'regular': 400, 
        'medium': 500, 
        'semi bold': 600, 
        'bold': 700, 
        'extra bold': 800, 
        'black': 900
    }
    
    standard_widths = {
        'ultra condensed': 1,
        'extra condensed': 2,
        'condensed': 3,
        'semi condensed': 4,
        'normal': 5,
        'semi expanded': 6,
        'expanded': 7,
        'extra expanded': 8,
        'ultra expanded': 9
    }
    
    # Get font weight and width
    font_weight_name = font_info['weight']['description'].lower()
    font_width_name = font_info['width']['description'].lower()
    
    # Create comparison bars
    weight_values = list(standard_weights.values())
    width_values = [val * 100 for val in standard_widths.values()]  # Scale for visibility
    
    # Highlight the font's position
    weight_colors = ['lightgray'] * len(standard_weights)
    width_colors = ['lightgray'] * len(standard_widths)
    
    if font_weight_name in standard_weights:
        weight_idx = list(standard_weights.keys()).index(font_weight_name)
        weight_colors[weight_idx] = 'darkblue'
    
    if font_width_name in standard_widths:
        width_idx = list(standard_widths.keys()).index(font_width_name)
        width_colors[width_idx] = 'darkred'
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot weight
    ax1.bar(list(standard_weights.keys()), weight_values, color=weight_colors)
    ax1.set_title(f"Font Weight: {font_weight_name.capitalize()}", fontsize=14)
    ax1.set_ylabel("Weight Value")
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    # Plot width
    ax2.bar(list(standard_widths.keys()), width_values, color=width_colors)
    ax2.set_title(f"Font Width: {font_width_name.capitalize()}", fontsize=14)
    ax2.set_ylabel("Width Value")
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save or display
    if output_dir:
        metrics_path = os.path.join(output_dir, f"{font_info['font_name'].replace(' ', '_')}_metrics.png")
        plt.savefig(metrics_path, dpi=300, bbox_inches='tight')
        visualization_paths['metrics_chart'] = metrics_path
        plt.close(fig)
    else:
        plt.show()
    
    # 3. Create a sample text rendering
    try:
        # Create a sample text image using the font
        font_path = font_info.get('font_path', '')
        if font_path and os.path.exists(font_path):
            # Sample text
            sample_text = "The quick brown fox jumps over the lazy dog."
            sample_heading = "ABCDEFGHIJKLM"
            
            # Create image
            img_width, img_height = 1000, 400
            img = Image.new('RGB', (img_width, img_height), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                # Load font at different sizes
                heading_font = ImageFont.truetype(font_path, 48)
                body_font = ImageFont.truetype(font_path, 24)
                
                # Draw text
                draw.text((50, 50), sample_heading, font=heading_font, fill='black')
                draw.text((50, 150), sample_text, font=body_font, fill='black')
                draw.text((50, 200), sample_text.upper(), font=body_font, fill='black')
                draw.text((50, 250), "0123456789", font=body_font, fill='black')
                
                # Add font info
                info_text = f"Font: {font_info['font_name']} | Weight: {font_info['weight']['description']} | Style: {font_info['style']}"
                draw.text((50, 320), info_text, fill='gray')
                
                # Save or display
                if output_dir:
                    sample_path = os.path.join(output_dir, f"{font_info['font_name'].replace(' ', '_')}_sample.png")
                    img.save(sample_path)
                    visualization_paths['text_sample'] = sample_path
                else:
                    # Convert to BytesIO for display
                    buf = BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    
                    # Display using matplotlib
                    plt.figure(figsize=(10, 4))
                    plt.imshow(np.array(img))
                    plt.axis('off')
                    plt.title(f"Sample Text: {font_info['font_name']}")
                    plt.tight_layout()
                    plt.show()
            except Exception as e:
                print(f"Error rendering font sample: {e}")
    except Exception as e:
        print(f"Error creating text sample: {e}")
    
    # 4. Create suitable use cases visualization
    if 'personality' in font_info and 'suitable_use_cases' in font_info['personality']:
        use_cases = font_info['personality']['suitable_use_cases']
        
        if 'suitable_for' in use_cases and use_cases['suitable_for']:
            # Get top use cases
            suitable = use_cases['suitable_for'][:5]  # Top 5
            less_suitable = use_cases.get('less_suitable_for', [])[:3]  # Top 3
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot suitable use cases in green
            for i, use_case in enumerate(suitable):
                ax.barh(i, 0.8, color='green', alpha=0.7)
                ax.text(0.1, i, use_case, ha='left', va='center', color='black')
            
            # Plot less suitable use cases in red (if any)
            offset = len(suitable) + 1  # Add a gap
            for i, use_case in enumerate(less_suitable):
                ax.barh(i + offset, 0.8, color='red', alpha=0.7)
                ax.text(0.1, i + offset, use_case, ha='left', va='center', color='black')
            
            # Set labels and title
            ax.set_yticks([])
            ax.set_xticks([])
            ax.set_xlim(0, 1)
            
            # Create legend
            legend_elements = [
                Patch(facecolor='green', alpha=0.7, label='Suitable For'),
                Patch(facecolor='red', alpha=0.7, label='Less Suitable For')
            ]
            ax.legend(handles=legend_elements, loc='upper right')
            
            ax.set_title(f"Recommended Use Cases: {font_info['font_name']}", fontsize=14)
            
            # Remove spines
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Save or display
            if output_dir:
                use_cases_path = os.path.join(output_dir, f"{font_info['font_name'].replace(' ', '_')}_use_cases.png")
                plt.savefig(use_cases_path, dpi=300, bbox_inches='tight')
                visualization_paths['use_cases'] = use_cases_path
                plt.close(fig)
            else:
                plt.tight_layout()
                plt.show()
    
    return visualization_paths

def create_font_report(font_info, output_dir):
    """
    Create a comprehensive visual report for a font.
    
    Args:
        font_info (dict): Dictionary containing font analysis results
        output_dir (str): Directory to save the report
        
    Returns:
        str: Path to the generated report HTML file
    """
    import matplotlib.pyplot as plt
    import os
    import base64
    from io import BytesIO
    from datetime import datetime
    
    # Create output directory if needed
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate visualizations
    viz_paths = visualize_font_properties(font_info, output_dir)
    
    # Convert absolute paths to filenames only for use in the HTML
    viz_filenames = {}
    if viz_paths:
        for key, path in viz_paths.items():
            viz_filenames[key] = os.path.basename(path)
    
    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Font Analysis Report: {font_info['font_name']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            .section {{
                margin-bottom: 40px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            .viz-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .viz-container img {{
                max-width: 100%;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                border-radius: 5px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }}
            .metric-item {{
                background-color: #fff;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .metric-value {{
                font-weight: bold;
                color: #3498db;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #7f8c8d;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Font Analysis Report: {font_info['font_name']}</h1>
            <p>Format: {font_info['format']} | Style: {font_info['style']}</p>
        </div>
        
        <div class="section">
            <h2>Font Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-item">
                    <p>Weight: <span class="metric-value">{font_info['weight']['description']} ({font_info['weight']['class']})</span></p>
                </div>
                <div class="metric-item">
                    <p>Width: <span class="metric-value">{font_info['width']['description']} ({font_info['width']['class']})</span></p>
                </div>
    """
    
    # Add stroke width if available
    if font_info['weight']['stroke_width'] is not None:
        html_content += f"""
                <div class="metric-item">
                    <p>Stroke Width: <span class="metric-value">{font_info['weight']['stroke_width']:.2f} units</span></p>
                </div>
                <div class="metric-item">
                    <p>Normalized Stroke Width: <span class="metric-value">{font_info['weight']['normalized_stroke_width']:.4f}</span></p>
                </div>
        """
    
    # Add aspect ratio if available
    if font_info['width']['aspect_ratio'] is not None:
        html_content += f"""
                <div class="metric-item">
                    <p>Aspect Ratio: <span class="metric-value">{font_info['width']['aspect_ratio']:.2f}</span></p>
                </div>
        """
    
    # Add shape information
    html_content += f"""
                <div class="metric-item">
                    <p>Shape: <span class="metric-value">{font_info['shape']['type']}</span></p>
                </div>
                <div class="metric-item">
                    <p>Spacing: <span class="metric-value">{font_info['spacing']['width_type']} width, {font_info['spacing']['spacing_type']} spacing</span></p>
                </div>
            </div>
            
            <div class="viz-container">
                <img src="{viz_filenames.get('metrics_chart', '')}" alt="Font Metrics Visualization">
            </div>
        </div>
    """
    
    # Add personality section if available
    if 'personality' in font_info:
        html_content += f"""
        <div class="section">
            <h2>Personality Analysis</h2>
        """
        
        if 'emotional_description' in font_info['personality']:
            html_content += f"""
            <p><strong>Emotional Description:</strong> {font_info['personality']['emotional_description']}</p>
            """
        
        html_content += f"""
            <div class="viz-container">
                <img src="{viz_filenames.get('personality_radar', '')}" alt="Font Personality Radar Chart">
            </div>
        """
        
        # Add use cases visualization if available
        if 'use_cases' in viz_paths:
            html_content += f"""
            <h3>Recommended Use Cases</h3>
            <div class="viz-container">
                <img src="{viz_filenames.get('use_cases', '')}" alt="Font Use Cases">
            </div>
            """
        
        html_content += """
        </div>
        """
    
    # Add sample text section if available
    if 'text_sample' in viz_paths:
        html_content += f"""
        <div class="section">
            <h2>Font Sample</h2>
            <div class="viz-container">
                <img src="{viz_filenames.get('text_sample', '')}" alt="Font Sample Text">
            </div>
        </div>
        """
    
    # Close HTML
    html_content += f"""
        <div class="footer">
            <p>Generated by Font Analyzer on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    
    # Write HTML to file
    report_path = os.path.join(output_dir, f"{font_info['font_name'].replace(' ', '_')}_report.html")
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    return report_path