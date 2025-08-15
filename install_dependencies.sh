#!/bin/bash

# Windows 11 to Windows 10 ISO Patcher - Dependency Installation Script
# This script installs all required dependencies for the ISO patcher

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_step() {
    echo -e "\n${YELLOW}► $1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS."
        print_error "The Windows 11 to Windows 10 ISO patcher is specifically for Intel Macs with Boot Camp."
        exit 1
    fi
}

# Check if Homebrew is installed
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew is not installed."
        echo "Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    print_success "✓ Homebrew is installed"
}

# Install system dependencies via Homebrew
install_system_dependencies() {
    print_step "Installing system dependencies..."
    
    # Update Homebrew
    print_step "Updating Homebrew..."
    brew update
    
    # Install required packages
    local packages=(
        "wimlib"      # For WIM file manipulation
        "hivex"       # For offline Windows registry editing
        "cdrtools"    # Provides mkisofs for ISO creation
        "pkg-config"  # Required for building some dependencies
    )
    
    for package in "${packages[@]}"; do
        print_step "Installing $package..."
        if brew list "$package" &> /dev/null; then
            print_success "✓ $package is already installed"
        else
            brew install "$package"
            print_success "✓ $package installed successfully"
        fi
    done
}

# Install Python dependencies
install_python_dependencies() {
    print_step "Installing Python dependencies..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Installing via Homebrew..."
        brew install python3
    fi
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install required Python packages
    local python_packages=(
        "pycdlib"     # For ISO manipulation
        "argparse"    # For command line parsing (usually built-in)
    )
    
    for package in "${python_packages[@]}"; do
        print_step "Installing Python package: $package"
        python3 -m pip install "$package"
        print_success "✓ $package installed successfully"
    done
}

# Verify installations
verify_dependencies() {
    print_step "Verifying installations..."
    
    local all_good=true
    
    # Check wimlib-imagex
    if command -v wimlib-imagex &> /dev/null; then
        wimlib_version=$(wimlib-imagex --version 2>&1 | head -n1 || echo "Unknown version")
        print_success "✓ wimlib-imagex found: $wimlib_version"
    else
        print_error "✗ wimlib-imagex not found"
        all_good=false
    fi
    
    # Check hivexsh
    if command -v hivexsh &> /dev/null; then
        print_success "✓ hivexsh found (registry editor)"
    else
        print_error "✗ hivexsh not found"
        all_good=false
    fi
    
    # Check mkisofs
    if command -v mkisofs &> /dev/null; then
        mkisofs_version=$(mkisofs -version 2>&1 | head -n1 || echo "Unknown version")
        print_success "✓ mkisofs found: $mkisofs_version"
    elif command -v genisoimage &> /dev/null; then
        print_success "✓ genisoimage found (ISO creation tool)"
    else
        print_warning "⚠ mkisofs/genisoimage not found (will use pycdlib fallback)"
    fi
    
    # Check pkg-config
    if command -v pkg-config &> /dev/null; then
        print_success "✓ pkg-config found"
    else
        print_warning "⚠ pkg-config not found"
    fi
    
    # Check Python packages
    print_step "Checking Python packages..."
    
    if python3 -c "import pycdlib" &> /dev/null; then
        pycdlib_version=$(python3 -c "import pycdlib; print(pycdlib.__version__)" 2>/dev/null || echo "Unknown version")
        print_success "✓ pycdlib found: $pycdlib_version"
    else
        print_error "✗ pycdlib not found"
        all_good=false
    fi
    
    if python3 -c "import argparse" &> /dev/null; then
        print_success "✓ argparse found"
    else
        print_error "✗ argparse not found"
        all_good=false
    fi
    
    # Final status
    if $all_good; then
        print_success "\n✓ All dependencies are installed and verified!"
        return 0
    else
        print_error "\n✗ Some dependencies are missing or not working properly."
        return 1
    fi
}

# Show usage instructions
show_usage() {
    print_header "Usage Instructions"
    
    echo "The Windows 11 to Windows 10 ISO Patcher is now ready to use!"
    echo ""
    echo "Usage:"
    echo "  python3 main.py <windows11_iso> <windows10_iso> [output_iso]"
    echo ""
    echo "Examples:"
    echo "  python3 main.py Win11_22H2_English_x64v1.iso Win10_22H2_English_x64.iso"
    echo "  python3 main.py Win11.iso Win10.iso patched_win11.iso"
    echo ""
    echo "What this tool does:"
    echo "  • Extracts version information from the Windows 10 ISO"
    echo "  • Applies Windows 10 identifiers to the Windows 11 ISO"
    echo "  • Bypasses TPM 2.0 and Secure Boot requirements"
    echo "  • Creates an ISO that Boot Camp recognizes as Windows 10"
    echo ""
    echo "Requirements:"
    echo "  • Two ISO files: Windows 11 (source) and Windows 10 (for metadata)"
    echo "  • At least 15GB of free disk space for temporary files"
    echo "  • Intel-based Mac with Boot Camp support"
    echo ""
    echo "After patching:"
    echo "  • Use the output ISO with Boot Camp Assistant"
    echo "  • Boot Camp will see it as Windows 10 and allow installation"
    echo "  • You'll get Windows 11 features once installed"
}

# Test function
test_tools() {
    print_header "Testing Tools"
    
    # Test wimlib-imagex
    print_step "Testing wimlib-imagex..."
    wimlib-imagex --help > /dev/null 2>&1
    print_success "✓ wimlib-imagex is working"
    
    # Test hivexsh  
    print_step "Testing hivexsh..."
    # hivexsh returns non-zero for --help but that's normal
    hivexsh --help > /dev/null 2>&1 || true
    print_success "✓ hivexsh is working"
    
    # Test mkisofs or genisoimage
    print_step "Testing ISO creation tools..."
    if command -v mkisofs &> /dev/null; then
        mkisofs -version > /dev/null 2>&1
        print_success "✓ mkisofs is working"
    elif command -v genisoimage &> /dev/null; then
        genisoimage -version > /dev/null 2>&1
        print_success "✓ genisoimage is working"
    else
        print_warning "⚠ No ISO creation tools found, will use Python fallback"
    fi
    
    # Test Python imports
    print_step "Testing Python imports..."
    python3 -c "import pycdlib; import tempfile; import pathlib; print('All Python modules imported successfully')"
    print_success "✓ Python modules are working"
    
    print_success "\n✓ All tools are working correctly!"
}

# Main installation process
main() {
    print_header "Windows 11 to Windows 10 ISO Patcher - Dependency Installer"
    
    echo "This script will install all required dependencies for the Windows 11 to Windows 10 ISO patcher."
    echo "The patcher creates Windows 11 ISOs that appear as Windows 10 to Boot Camp."
    echo ""
    
    # Check if user wants to continue
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    # Run installation steps
    check_macos
    check_homebrew
    install_system_dependencies
    install_python_dependencies
    
    echo ""
    print_header "Verification"
    
    if verify_dependencies; then
        echo ""
        print_header "Testing"
        test_tools
        
        echo ""
        show_usage
        
        print_header "Installation Complete!"
        print_success "✓ All dependencies installed and verified successfully!"
        print_success "✓ You can now run the Windows 11 to Windows 10 ISO patcher."
        
    else
        print_header "Installation Issues"
        print_error "Some dependencies could not be installed or verified."
        print_error "Please check the output above for specific errors."
        echo ""
        echo "Common fixes:"
        echo "  • Make sure you have sufficient permissions"
        echo "  • Try running: brew doctor"
        echo "  • Update macOS to the latest version"
        echo "  • Restart your terminal and try again"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "--test")
        check_macos
        verify_dependencies
        test_tools
        ;;
    "--verify")
        check_macos
        verify_dependencies
        ;;
    "--help"|"-h")
        echo "Windows 11 to Windows 10 ISO Patcher - Dependency Installer"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no option)  Run full installation"
        echo "  --test       Test installed tools"
        echo "  --verify     Verify dependencies only"
        echo "  --help       Show this help"
        ;;
    *)
        main
        ;;
esac 