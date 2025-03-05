# Contributing to Font Validator

Thank you for considering contributing to Font Validator! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in the Issues section
- Use the bug report template when creating a new issue
- Include detailed steps to reproduce the bug
- Include information about your environment (OS, Python version, etc.)
- Include screenshots if applicable

### Suggesting Enhancements

- Check if the enhancement has already been suggested in the Issues section
- Use the feature request template when creating a new issue
- Clearly describe the enhancement and its benefits
- Provide examples of how the enhancement would work

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Submit a pull request

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/font-validator.git
   cd font-validator
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests
   ```bash
   python -m unittest discover tests
   ```

## Coding Guidelines

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Add unit tests for new functionality
- Keep functions small and focused on a single task
- Use meaningful variable and function names

## Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in the present tense (e.g., "Add feature" not "Added feature")
- Reference issue numbers when applicable

## Documentation

- Update the README.md file with any necessary changes
- Add or update docstrings for any modified code
- Update the SUMMARY.md file if applicable

Thank you for your contributions! 