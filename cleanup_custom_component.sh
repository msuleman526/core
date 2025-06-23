#!/bin/bash

# Backup any custom files first
echo "Creating backup of custom_components/custom_dashboard"
mkdir -p backup/custom_components
cp -r config/custom_components/custom_dashboard backup/custom_components/ 2>/dev/null

# Create backup of storage file
echo "Backing up storage file"
mkdir -p backup/.storage
cp config/.storage/custom_dashboard_3d_plan backup/.storage/ 2>/dev/null

# Remove the custom component directory
echo "Removing custom_components/custom_dashboard"
rm -rf config/custom_components/custom_dashboard

# Remove the storage file
echo "Removing custom_dashboard_3d_plan storage file"
rm -f config/.storage/custom_dashboard_3d_plan

echo "Cleanup complete!"
echo "Files have been backed up to ./backup/ directory"
echo "The custom component has been removed"
