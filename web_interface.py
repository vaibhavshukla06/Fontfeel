#!/usr/bin/env python3
"""
Font Validator Web Interface

This module provides a web interface for the Font Validator tool,
allowing users to upload and analyze fonts through a browser.
"""

# Set the Matplotlib backend to 'Agg' (non-interactive) for web application use
import matplotlib
matplotlib.use('Agg')

import os
import tempfile
import uuid
import traceback
import logging
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
import werkzeug.exceptions

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import font validator modules
from font_validator import extract_font_properties, visualize_font_properties, create_font_report

# Check for variable font support
try:
    from variable_font_support import is_variable_font
    VARIABLE_FONT_SUPPORT = True
except ImportError:
    VARIABLE_FONT_SUPPORT = False
    
# Check for non-Latin script support
try:
    from non_latin_support import analyze_non_latin_support
    NON_LATIN_SUPPORT = True
except ImportError:
    NON_LATIN_SUPPORT = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_font_validator')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Configure upload folder
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'font_validator_uploads')
RESULTS_FOLDER = os.path.join(tempfile.gettempdir(), 'font_validator_results')
ALLOWED_EXTENSIONS = {'ttf', 'otf', 'woff', 'woff2'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

logger.info(f"Upload folder: {UPLOAD_FOLDER}")
logger.info(f"Results folder: {RESULTS_FOLDER}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page."""
    logger.info("Rendering index page")
    return render_template('index.html', 
                          variable_font_support=VARIABLE_FONT_SUPPORT,
                          non_latin_support=NON_LATIN_SUPPORT)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle font file uploads."""
    logger.info("Upload route called")
    
    try:
        # Check if the post request has the file part
        if 'font_file' not in request.files:
            logger.warning("No file part in request")
            flash('No file part')
            return redirect(url_for('index'))
        
        file = request.files['font_file']
        if file.filename == '':
            logger.warning("No selected file")
            flash('No selected file')
            return redirect(url_for('index'))
        
        if file and allowed_file(file.filename):
            # Generate a unique filename to prevent collisions
            unique_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            filename = f"{unique_id}_{original_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            logger.info(f"Saving file to {filepath}")
            file.save(filepath)
            
            # Get analysis options from form
            options = {}
            try:
                options = {
                    'generate_visualization': 'generate_viz' in request.form,
                    'generate_report': 'generate_report' in request.form,
                    'variable_only': 'variable_only' in request.form and VARIABLE_FONT_SUPPORT,
                    'analyze_non_latin': 'analyze_non_latin' in request.form and NON_LATIN_SUPPORT
                }
                logger.info(f"Analysis options: {options}")
            except Exception as e:
                logger.warning(f"Error parsing form options: {str(e)}")
                # Use default options if form parsing fails
                options = {
                    'generate_visualization': True,
                    'generate_report': True,
                    'variable_only': False,
                    'analyze_non_latin': False
                }
                logger.info(f"Using default options: {options}")
            
            # Process the font file
            return redirect(url_for('analyze_font', filename=filename, **options))
        
        logger.warning(f"Invalid file type: {file.filename}")
        flash('Invalid file type. Allowed types: TTF, OTF, WOFF, WOFF2')
        return redirect(url_for('index'))
    
    except werkzeug.exceptions.ClientDisconnected as e:
        logger.error(f"Client disconnected during upload: {str(e)}")
        flash('Upload was interrupted. Please try again.')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))

@app.route('/analyze/<filename>')
def analyze_font(filename):
    """Analyze the uploaded font file and display results."""
    logger.info(f"Analyze route called for file: {filename}")
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Checking file at path: {filepath}")
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            flash('File not found')
            return redirect(url_for('index'))
        
        # Check if variable font only option is enabled
        variable_only = request.args.get('variable_only', 'false').lower() == 'true'
        
        # If variable only is enabled, check if the font is variable
        if variable_only and VARIABLE_FONT_SUPPORT:
            logger.info("Checking if font is variable")
            if not is_variable_font(filepath):
                logger.warning("Font is not a variable font")
                flash('The uploaded font is not a variable font')
                return redirect(url_for('index'))
        
        # Extract font properties
        logger.info("Extracting font properties")
        font_properties = extract_font_properties(filepath)
        
        if not font_properties:
            logger.error("Failed to analyze font")
            flash('Failed to analyze font')
            return redirect(url_for('index'))
        
        # Generate visualizations if requested
        viz_paths = {}
        if request.args.get('generate_visualization', 'false').lower() == 'true':
            logger.info("Generating visualizations")
            output_dir = os.path.join(app.config['RESULTS_FOLDER'], filename.split('.')[0])
            os.makedirs(output_dir, exist_ok=True)
            full_viz_paths = visualize_font_properties(font_properties, output_dir)
            
            # Convert the full paths to paths relative to RESULTS_FOLDER for the template
            if full_viz_paths:
                viz_paths = {k: os.path.relpath(v, app.config['RESULTS_FOLDER']) for k, v in full_viz_paths.items()}
                logger.info(f"Visualizations generated: {list(viz_paths.keys())}")
                # Log each visualization path for debugging
                for viz_type, viz_path in viz_paths.items():
                    logger.info(f"Visualization {viz_type}: {viz_path}")
                    logger.info(f"Full path: {os.path.join(app.config['RESULTS_FOLDER'], viz_path)}")
                    logger.info(f"File exists: {os.path.exists(os.path.join(app.config['RESULTS_FOLDER'], viz_path))}")
        
        # Generate report if requested
        report_path = None
        if request.args.get('generate_report', 'false').lower() == 'true' and viz_paths:
            logger.info("Generating report")
            # Create the output directory for the report
            report_output_dir = os.path.join(app.config['RESULTS_FOLDER'], filename.split('.')[0])
            full_report_path = create_font_report(font_properties, report_output_dir)
            
            # Convert the full path to a path relative to RESULTS_FOLDER for the template
            if full_report_path:
                report_path = os.path.relpath(full_report_path, app.config['RESULTS_FOLDER'])
                logger.info(f"Report generated at: {report_path}")
                logger.info(f"Full report path: {os.path.join(app.config['RESULTS_FOLDER'], report_path)}")
                logger.info(f"Report file exists: {os.path.exists(os.path.join(app.config['RESULTS_FOLDER'], report_path))}")
        
        # Render the results page
        logger.info("Rendering results page")
        return render_template('results.html', 
                              font_properties=font_properties,
                              viz_paths=viz_paths,
                              report_path=report_path,
                              filename=filename)
    
    except Exception as e:
        logger.error(f"Error in analyze_font: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))

@app.route('/results/<path:filename>')
def download_file(filename):
    """Serve generated files."""
    logger.info(f"Download route called for file: {filename}")
    try:
        # Log the full path being requested
        full_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        logger.info(f"Attempting to serve file from: {full_path}")
        
        # Check if the file exists
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return f"File not found: {filename}", 404
            
        return send_from_directory(app.config['RESULTS_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error in download_file: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for font analysis."""
    logger.info("API analyze route called")
    
    try:
        if 'font_file' not in request.files:
            logger.warning("No file part in API request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['font_file']
        if file.filename == '':
            logger.warning("No selected file in API request")
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Generate a unique filename to prevent collisions
            unique_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            filename = f"{unique_id}_{original_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            logger.info(f"Saving API file to {filepath}")
            file.save(filepath)
            
            # Extract font properties
            logger.info("Extracting font properties for API request")
            font_properties = extract_font_properties(filepath)
            
            if not font_properties:
                logger.error("Failed to analyze font for API request")
                return jsonify({'error': 'Failed to analyze font'}), 500
            
            return jsonify({
                'success': True,
                'font_properties': font_properties
            })
        
        logger.warning(f"Invalid file type in API request: {file.filename}")
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        logger.error(f"Error in api_analyze: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/compare')
def compare_fonts():
    """Render the font comparison page."""
    logger.info("Rendering compare fonts page")
    return render_template('compare.html',
                          variable_font_support=VARIABLE_FONT_SUPPORT,
                          non_latin_support=NON_LATIN_SUPPORT)

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True, port=5001) 