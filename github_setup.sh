#!/bin/bash

# Initialize Git repository
git init

# Add all files to Git
git add .

# Create initial commit
git commit -m "Initial commit"

# Instructions for connecting to GitHub
echo "
Repository is now ready for GitHub upload!

To connect to GitHub, follow these steps:

1. Create a new repository on GitHub (without README, .gitignore, or license)
2. Run the following commands:

   git remote add origin https://github.com/yourusername/font-validator.git
   git branch -M main
   git push -u origin main

Replace 'yourusername' with your actual GitHub username.
"

# Make the script executable
chmod +x github_setup.sh 