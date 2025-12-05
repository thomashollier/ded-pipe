#!/bin/bash

# Debian WSL Setup Script with Homebrew
# This script sets up a basic development environment on Debian WSL

set -e  # Exit on error

echo "=================================="
echo "Debian WSL Setup Script"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check if running on WSL
if ! grep -qi microsoft /proc/version; then
    print_error "This script is designed for WSL (Windows Subsystem for Linux)"
    print_info "Continuing anyway, but some features may not work as expected..."
fi

# Update and upgrade system packages
print_info "Updating system packages..."

# Remove bullseye-backports if present (no longer available)
if grep -q "bullseye-backports" /etc/apt/sources.list 2>/dev/null; then
    print_info "Removing obsolete bullseye-backports repository..."
    sudo sed -i '/bullseye-backports/d' /etc/apt/sources.list
fi

sudo apt update
sudo apt upgrade -y
print_status "System packages updated"

# Install essential build tools and dependencies
print_info "Installing essential build tools..."
sudo apt install -y \
    build-essential \
    procps \
    curl \
    file \
    git \
    wget \
    ca-certificates \
    gnupg \
    lsb-release
print_status "Essential build tools installed"

# Install Homebrew
print_info "Installing Homebrew for Linux..."
if command -v brew &> /dev/null; then
    print_info "Homebrew is already installed"
else
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH
    print_info "Configuring Homebrew in shell profile..."
    
    # Detect the Homebrew installation path
    if [ -d "/home/linuxbrew/.linuxbrew" ]; then
        BREW_PREFIX="/home/linuxbrew/.linuxbrew"
    elif [ -d "$HOME/.linuxbrew" ]; then
        BREW_PREFIX="$HOME/.linuxbrew"
    else
        print_error "Could not find Homebrew installation"
        exit 1
    fi
    
    # Add to bash profile
    if ! grep -q "eval.*brew shellenv" "$HOME/.bashrc"; then
        echo '' >> "$HOME/.bashrc"
        echo '# Homebrew' >> "$HOME/.bashrc"
        echo "eval \"\$($BREW_PREFIX/bin/brew shellenv)\"" >> "$HOME/.bashrc"
    fi
    
    # Add to current session
    eval "$($BREW_PREFIX/bin/brew shellenv)"
    
    print_status "Homebrew installed successfully"
fi

# Verify Homebrew installation
if command -v brew &> /dev/null; then
    print_status "Homebrew version: $(brew --version | head -n 1)"
else
    print_error "Homebrew installation failed"
    exit 1
fi

# Run brew doctor to check installation
print_info "Running brew doctor..."
brew doctor || true

# Update Homebrew
print_info "Updating Homebrew..."
brew update
print_status "Homebrew updated"

# Install common useful packages via Homebrew
print_info "Installing common Homebrew packages..."
brew install \
    gcc \
    git \
    curl \
    wget
print_status "Common packages installed"

# Install media and color management tools
print_info "Installing OpenColorIO (OCIO)..."
brew install opencolorio
print_status "OpenColorIO installed"

print_info "Installing OpenImageIO (OIIO)..."
brew install openimageio
print_status "OpenImageIO installed"

print_info "Installing FFmpeg..."
brew install ffmpeg
print_status "FFmpeg installed"

print_info "Installing MediaInfo..."
brew install mediainfo
print_status "MediaInfo installed"

# Install pyenv for Python version management
print_info "Installing pyenv..."
brew install pyenv

# Add pyenv to bashrc
if ! grep -q "PYENV_ROOT" "$HOME/.bashrc"; then
    echo '' >> "$HOME/.bashrc"
    echo '# pyenv' >> "$HOME/.bashrc"
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$HOME/.bashrc"
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'eval "$(pyenv init -)"' >> "$HOME/.bashrc"
fi

# Initialize pyenv for current session
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

print_status "pyenv installed"

# Install Python build dependencies
print_info "Installing Python build dependencies..."
sudo apt install -y \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    libncurses5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    lzma
print_status "Python build dependencies installed"

# Install Python 3.12 via pyenv
print_info "Installing Python 3.12 via pyenv (this may take a few minutes)..."
pyenv install 3.12 -s
print_status "Python 3.12 installed"

# Set Python 3.12 as global default
print_info "Setting Python 3.12 as global default..."
pyenv global 3.12
print_status "Python 3.12 set as default"

# Verify Python installation
print_info "Python version: $(python --version)"
print_info "pip version: $(pip --version)"

# Install ACES 1.3 configuration to Windows C: drive
print_info "Downloading and installing ACES 1.3 configuration..."
ACES_DIR="/mnt/c/ACES"
sudo mkdir -p "$ACES_DIR"

# Download ACES 1.3 Studio Config (includes all camera input transforms)
cd /tmp
print_info "Downloading ACES Studio Config v2.2.0 for ACES 1.3..."
print_info "This includes camera transforms for Sony Venice, ARRI, RED, Canon, etc."

# Download the Studio config (includes S-Log3/S-Gamut3 for Venice 2)
wget -O studio-config-v2.2.0_aces-v1.3_ocio-v2.4.ocio \
    https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/releases/download/v2.1.0-v2.2.0/studio-config-v2.2.0_aces-v1.3_ocio-v2.4.ocio

# Create directory structure
sudo mkdir -p "$ACES_DIR/aces_1.3"

# Move config file as the main config
sudo mv studio-config-v2.2.0_aces-v1.3_ocio-v2.4.ocio "$ACES_DIR/aces_1.3/config.ocio"

print_status "ACES 1.3 Studio Configuration installed to C:\\ACES\\aces_1.3\\config.ocio"

# Also download CG config as an alternative (lighter, no camera transforms)
print_info "Downloading ACES CG Config (optional, lighter config without camera transforms)..."
wget -O cg-config-v2.2.0_aces-v1.3_ocio-v2.4.ocio \
    https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/releases/download/v2.1.0-v2.2.0/cg-config-v2.2.0_aces-v1.3_ocio-v2.4.ocio

sudo mv cg-config-v2.2.0_aces-v1.3_ocio-v2.4.ocio "$ACES_DIR/aces_1.3/cg-config.ocio"

print_status "ACES 1.3 CG Configuration also installed (optional)"
print_info "To use CG config instead, set OCIO to: C:\\ACES\\aces_1.3\\cg-config.ocio"

print_info ""
print_info "Available Sony Venice colorspaces in Studio config:"
print_info "  - S-Log3 S-Gamut3"
print_info "  - S-Log3 S-Gamut3.Cine"
print_info "  - Linear S-Gamut3"
print_info "  - Linear S-Gamut3.Cine"
print_info "  - Linear Venice S-Gamut3"

# Set up OCIO environment variable for WSL
if ! grep -q "OCIO=" "$HOME/.bashrc"; then
    echo '' >> "$HOME/.bashrc"
    echo '# OpenColorIO ACES Configuration' >> "$HOME/.bashrc"
    echo "export OCIO=\"/mnt/c/ACES/aces_1.3/config.ocio\"" >> "$HOME/.bashrc"
fi

export OCIO="/mnt/c/ACES/aces_1.3/config.ocio"
print_status "OCIO environment variable configured for WSL"

# Download Sony RAW Media Exporter info
print_info "Sony RAW Media Exporter setup:"
print_info "  1. Download from: https://www.sony.com/electronics/support/downloads"
print_info "  2. Install on Windows normally"
print_info "  3. Use the provided BAT file to run with proper environment variables"
print_status "Sony RAW exporter can be called from Windows BAT files"

# Clean up
print_info "Cleaning up..."
sudo apt autoremove -y
sudo apt clean
brew cleanup
print_status "Cleanup complete"

echo ""
echo "=================================="
print_status "Setup Complete!"
echo "=================================="
echo ""
echo "Installed Components:"
echo "  - Homebrew: $(brew --prefix)"
echo "  - pyenv (Python version manager)"
echo "  - Python 3.12 (via pyenv, set as default)"
echo "  - OpenColorIO (OCIO)"
echo "  - OpenImageIO (OIIO)"
echo "  - FFmpeg"
echo "  - MediaInfo"
echo "  - ACES 1.3 Configuration"
echo ""
echo "Python (via pyenv):"
echo "  python --version  → Python 3.12.x"
echo "  pip --version     → pip for Python 3.12"
echo "  pyenv versions    → List installed Python versions"
echo "  pyenv install -l  → List available Python versions"
echo ""
echo "ACES Configuration:"
echo "  WSL Location: /mnt/c/ACES/aces_1.3/"
echo "  Windows Location: C:\\ACES\\aces_1.3\\"
echo "  OCIO variable: Set in ~/.bashrc for WSL"
echo ""
echo "Sony RAW Media Exporter:"
echo "  Download and install on Windows from:"
echo "  https://www.sony.com/electronics/support/downloads"
echo "  Use the provided BAT file to run with environment variables"
echo ""
echo "IMPORTANT: To activate all changes, run:"
echo "  source ~/.bashrc"
echo ""
echo "Or close and reopen your terminal."
echo ""
echo "Verify installations:"
echo "  brew --version"
echo "  python --version"
echo "  pip --version"
echo "  ffmpeg -version"
echo "  ociocheck"
echo ""
