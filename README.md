# Font Validator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A comprehensive tool for analyzing font files and providing detailed insights about their properties, personality traits, and recommended use cases.

## 🚀 Features

- **Detailed Font Analysis**: Extract and analyze font properties including style, weight, width, shape, and spacing.
- **Personality Insights**: Understand the emotional impact and personality traits conveyed by your fonts.
- **Use Case Recommendations**: Get suggestions for the best applications and contexts for your fonts.
- **Visual Reports**: Generate visualizations and comprehensive HTML reports.
- **Variable Font Support**: Analyze variable fonts and their design spaces.
- **Non-Latin Script Support**: Evaluate font support for various writing systems.
- **Web Interface**: Upload and analyze fonts through a user-friendly web interface.

## 📋 Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/font-validator.git
cd font-validator

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🎮 Usage

### Command Line Interface

```bash
# Analyze a single font file
python font_analyzer_cli.py --font-path path/to/your/font.ttf

# Analyze a directory of fonts
python font_analyzer_cli.py --font-path path/to/your/fonts/

# Generate visualizations
python font_analyzer_cli.py --font-path path/to/your/font.ttf --generate-viz

# Generate HTML report
python font_analyzer_cli.py --font-path path/to/your/font.ttf --generate-report

# Analyze only variable fonts
python font_analyzer_cli.py --font-path path/to/your/fonts/ --variable-only

# Analyze non-Latin script support
python font_analyzer_cli.py --font-path path/to/your/font.ttf --analyze-non-latin
```

### Web Interface

```bash
# Start the web server
python web_interface.py
```

Then open your browser and navigate to `http://localhost:5000`.

## 📥 Download Variable Fonts for Testing

The repository includes a script to download variable fonts for testing:

```bash
python download_variable_fonts.py
```

This will download a selection of variable fonts from Google Fonts to a `variable_fonts` directory.

## 🧩 Project Structure

- `font_validator.py`: Core module with font analysis functions
- `font_analyzer_cli.py`: Command-line interface
- `web_interface.py`: Web interface using Flask
- `variable_font_support.py`: Module for variable font analysis
- `non_latin_support.py`: Module for non-Latin script support
- `download_variable_fonts.py`: Utility to download variable fonts for testing
- `templates/`: HTML templates for the web interface
- `static/`: CSS and other static assets
- `fonts/`: Sample fonts for testing
- `font_reports/`: Generated HTML reports
- `font_visualizations/`: Generated visualizations

## 📚 Dependencies

- fonttools
- numpy
- matplotlib
- seaborn
- pillow
- flask
- requests
- brotli (for WOFF2 support)
- zopfli (for WOFF compression)

## 🔜 Roadmap

### Phase 1: Research
- Continue expanding typography research
- Study more variable font capabilities
- Research additional non-Latin scripts and their requirements

### Phase 2: Enhancements
- Add support for more variable font features
- Enhance non-Latin script analysis
- Develop a more comprehensive web interface
- Create an API for third-party integration

### Phase 3: Testing
- Expand test suite with more diverse fonts
- Benchmark performance with large font libraries
- Test with edge cases and unusual font formats

### Phase 4: Documentation
- Create detailed API documentation
- Develop user guides for different use cases
- Add more examples and tutorials

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FontTools](https://github.com/fonttools/fonttools) for the font parsing library
- [Google Fonts](https://fonts.google.com/) for providing open-source fonts for testing
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for visualization capabilities 