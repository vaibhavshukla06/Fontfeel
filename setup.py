from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="font-validator",
    version="0.1.0",
    author="Font Validator Team",
    author_email="your.email@example.com",
    description="A comprehensive tool for analyzing font files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/font-validator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "font-validator=font_analyzer_cli:main",
        ],
    },
    include_package_data=True,
) 