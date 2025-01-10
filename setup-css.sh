#!/bin/bash

# Base directory for styles
BASE_DIR="assets/styles"

# Array of directories to create
directories=(
    "$BASE_DIR/settings"
    "$BASE_DIR/tools"
    "$BASE_DIR/generic"
    "$BASE_DIR/components"
    "$BASE_DIR/utilities"
)

# Array of files to create with their paths
declare -A files=(
    ["$BASE_DIR/settings/_variables.css"]=""
    ["$BASE_DIR/settings/_colors.css"]=""
    ["$BASE_DIR/settings/_typography.css"]=""
    ["$BASE_DIR/settings/_spacing.css"]=""
    ["$BASE_DIR/tools/_mixins.css"]=""
    ["$BASE_DIR/generic/_reset.css"]=""
    ["$BASE_DIR/generic/_bootstrap-override.css"]=""
    ["$BASE_DIR/components/_buttons.css"]=""
    ["$BASE_DIR/components/_dropdowns.css"]=""
    ["$BASE_DIR/components/_sidebar.css"]=""
    ["$BASE_DIR/components/_navbar.css"]=""
    ["$BASE_DIR/components/_data-table.css"]=""
    ["$BASE_DIR/utilities/_helpers.css"]=""
    ["$BASE_DIR/main.css"]=""
)

# Create directories
echo "Creating directories..."
for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo "Created directory: $dir"
done

# Create files
echo -e "\nCreating files..."
for file in "${!files[@]}"; do
    touch "$file"
    echo "Created file: $file"
done

# Create main.css content with imports
echo "/* Settings */
@import './settings/_variables.css';
@import './settings/_colors.css';
@import './settings/_typography.css';
@import './settings/_spacing.css';

/* Tools */
@import './tools/_mixins.css';

/* Generic */
@import './generic/_reset.css';
@import './generic/_bootstrap-override.css';

/* Components */
@import './components/_buttons.css';
@import './components/_dropdowns.css';
@import './components/_sidebar.css';
@import './components/_navbar.css';
@import './components/_data-table.css';

/* Utilities */
@import './utilities/_helpers.css';" > "$BASE_DIR/main.css"

# Set permissions
echo -e "\nSetting permissions..."
chmod -R 644 "$BASE_DIR"/*
chmod 755 "$BASE_DIR" "${directories[@]}"

echo -e "\nSetup complete! CSS architecture created successfully."

# Optional: Backup existing CSS files
echo -e "\nBacking up existing CSS files..."
mkdir -p assets/backup
cp -v assets/*.css assets/backup/ 2>/dev/null || echo "No existing CSS files found"

echo -e "\nDone! New CSS architecture is ready to use."