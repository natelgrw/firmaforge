#!/bin/bash
# ==========================================
# analyze_all_firmware_docker.sh
# Author: @natelgrw
# Last Edited: 11/30/2025
#
# A script that analyzes all firmware files in the 
# demo_firmware directory and saves the results 
# to the results directory.
# ==========================================

set -e

# colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Building Docker image (if needed)..."
docker build -t firmaforge:latest . || {
    echo "Error: Failed to build Docker image."
    exit 1
}

echo -e "\n${GREEN}Starting firmware analysis in Docker...${NC}\n"

# create results directory
mkdir -p results

# run analysis for each firmware file
for firmware in demo_firmware/*; do
    if [ -f "$firmware" ] && [[ ! "$firmware" =~ [Tt][Pp][Ll][Ii][Nn][Kk] ]]; then
        firmware_name=$(basename "$firmware")
        echo "=========================================="
        echo "Analyzing: $firmware_name"
        echo "=========================================="
        
        firmware_basename=$(basename "$firmware" .${firmware##*.})
        docker run --rm \
            -v "$(pwd):/workspace" \
            -w /workspace \
            firmaforge:latest \
            python3 -c "from firmaforge import summarize_results; summarize_results.analyze_firmware('/workspace/$firmware', results_dir='/workspace/results')"
        
        echo ""
    fi
done

echo -e "\n${GREEN}Analysis complete${NC}"
echo "Results saved in: $(pwd)/results/"


