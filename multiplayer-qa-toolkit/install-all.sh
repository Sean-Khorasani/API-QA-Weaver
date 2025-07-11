#!/bin/bash

echo "=== Installing Epic Games Multiplayer QA Toolkit ==="
echo

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo -e "${GREEN}✓ Python $python_version is installed${NC}"
else
    echo -e "${RED}✗ Python 3.8+ is required. Found: $python_version${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo
echo "Upgrading pip..."
pip install --upgrade pip

# Install base requirements
echo
echo "Installing base requirements..."
cat > requirements-base.txt << EOF
numpy==1.24.3
asyncio==3.4.3
aiohttp==3.8.4
pyyaml==6.0
rich==13.3.5
matplotlib==3.7.1
pandas==2.0.2
pytest==7.3.1
pytest-asyncio==0.21.0
EOF

pip install -r requirements-base.txt

# Install tool-specific requirements
tools=(
    "network-simulator"
    "prediction-tester"
    "lag-compensation"
    "api-loadtest"
    "packet-analyzer"
    "chaos-testing"
)

echo
echo "Installing tool-specific dependencies..."
echo

for tool in "${tools[@]}"; do
    if [ -d "$tool" ]; then
        echo "Installing $tool dependencies..."
        if [ -f "$tool/requirements.txt" ]; then
            pip install -r "$tool/requirements.txt"
            echo -e "${GREEN}✓ $tool dependencies installed${NC}"
        else
            echo -e "${RED}✗ No requirements.txt found for $tool${NC}"
        fi
    else
        echo -e "${RED}✗ Directory $tool not found${NC}"
    fi
    echo
done

# Create common utilities directory
echo "Setting up common utilities..."
mkdir -p common

# Create __init__.py files
touch common/__init__.py
touch integration/__init__.py

# Make demo scripts executable
echo
echo "Making scripts executable..."
find . -name "*.py" -type f -exec chmod +x {} \;
chmod +x install-all.sh

# Create results directory
echo
echo "Creating results directory..."
mkdir -p results

# Verify installation
echo
echo "Verifying installation..."
echo

# Test imports
python3 -c "
try:
    import numpy
    import asyncio
    import aiohttp
    import yaml
    import rich
    print('✓ Core dependencies verified')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
    exit(1)
"

# Create quick start script
cat > quickstart.py << 'EOF'
#!/usr/bin/env python3
"""Quick start guide for Epic Games Multiplayer QA Toolkit"""

import sys
import os

def main():
    print("=== Epic Games Multiplayer QA Toolkit Quick Start ===\n")
    
    tools = {
        '1': ('Network Simulator', 'network-simulator/network_simulator.py'),
        '2': ('Prediction Tester', 'prediction-tester/prediction_tester.py'),
        '3': ('Lag Compensation', 'lag-compensation/lag_compensation_tester.py'),
        '4': ('API Load Test', 'api-loadtest/api_loadtest.py'),
        '5': ('Packet Analyzer', 'packet-analyzer/packet_analyzer.py'),
        '6': ('Chaos Testing', 'chaos-testing/chaos_testing.py'),
        '7': ('Integrated Suite', 'integration/integrated_test_suite.py')
    }
    
    print("Available tools:")
    for key, (name, _) in tools.items():
        print(f"{key}. {name}")
    
    choice = input("\nSelect a tool to run (1-7): ")
    
    if choice in tools:
        name, script = tools[choice]
        print(f"\nRunning {name}...\n")
        os.system(f"python {script}")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
EOF

chmod +x quickstart.py

# Summary
echo
echo "==================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "==================================="
echo
echo "Virtual environment: venv/"
echo "Results directory: results/"
echo
echo "To get started:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run quick start: ./quickstart.py"
echo "3. Or run individual tools:"
echo "   - python network-simulator/network_simulator.py"
echo "   - python prediction-tester/prediction_tester.py"
echo "   - python lag-compensation/lag_compensation_tester.py"
echo "   - python api-loadtest/api_loadtest.py"
echo "   - python packet-analyzer/packet_analyzer.py"
echo "   - python chaos-testing/chaos_testing.py"
echo "   - python integration/integrated_test_suite.py"
echo
echo "For detailed documentation, see README.md"
echo