#!/bin/bash

# Windows 11 Boot Camp ISO Patcher v3 Launch Script
# v3: Uses WinPE injection approach - replaces Windows 11 boot.wim with Windows 10 boot.wim

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE} Windows 11 Boot Camp ISO Patcher v3${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE} WinPE Injection Method${NC}"
echo -e "${BLUE} • Extracts Windows 10 WinPE${NC}"
echo -e "${BLUE} • Injects into Windows 11 ISO${NC}"
echo -e "${BLUE} • Boot Camp sees Windows 10${NC}"
echo -e "${BLUE} • Actually installs Windows 11${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📍 Working directory: ${SCRIPT_DIR}${NC}"
echo ""

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found in current directory${NC}"
    echo -e "${RED}   Please run this script from the project directory${NC}"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed or not in PATH${NC}"
    echo -e "${YELLOW}   Please install Python 3 first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

# Check dependencies (but don't fail if missing)
echo -e "${YELLOW}🔍 Checking dependencies for WinPE injection...${NC}"

MISSING_DEPS=()

# Check system dependencies
if ! command -v wimlib-imagex &> /dev/null; then
    MISSING_DEPS+=("wimlib-imagex (for WIM extraction/modification)")
fi

if ! command -v hivexsh &> /dev/null; then
    MISSING_DEPS+=("hivexsh (for TPM bypass registry entries)")
fi

if ! command -v mkisofs &> /dev/null && ! command -v genisoimage &> /dev/null; then
    MISSING_DEPS+=("mkisofs/genisoimage (for ISO creation)")
fi

# Check Python dependencies
if ! python3 -c "import pycdlib" 2>/dev/null; then
    MISSING_DEPS+=("pycdlib (for ISO extraction)")
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    MISSING_DEPS+=("tkinter (for GUI)")
fi

# Report missing dependencies but continue
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Missing dependencies detected:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo -e "${YELLOW}   - $dep${NC}"
    done
    echo ""
    echo -e "${YELLOW}📝 To install missing dependencies, run:${NC}"
    echo -e "${BLUE}   ./install_dependencies.sh${NC}"
    echo ""
    echo -e "${YELLOW}⏳ Launching v3 app anyway (WinPE injection may not work without dependencies)...${NC}"
else
    echo -e "${GREEN}✅ All dependencies found!${NC}"
    echo -e "${GREEN}🚀 Launching Windows 11 Boot Camp ISO Patcher v3...${NC}"
fi

echo ""

# Always launch the application (don't let dependency issues prevent launching)
echo -e "${BLUE}Starting v3 application with WinPE injection...${NC}"
python3 main.py

echo ""
echo -e "${BLUE}👋 Application closed${NC}"
