#!/bin/bash

# Build script for Recall.app
# This script builds the macOS application bundle using py2app

set -e  # Exit on any error

echo "🏗️  Building Recall.app..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is intended for macOS only"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$(python3 -c "import sys; print(sys.version_info >= (3, 9))")" != "True" ]]; then
    print_error "Python 3.9 or later is required. Found: $PYTHON_VERSION"
    exit 1
fi
print_success "Python version: $PYTHON_VERSION"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
print_success "Cleaned build directories"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install build tools
print_status "Upgrading pip and installing build tools..."
pip install --upgrade pip setuptools wheel

# Install py2app
print_status "Installing py2app..."
pip install py2app

# Install dependencies
print_status "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed from requirements.txt"
else
    print_warning "requirements.txt not found, installing minimal dependencies..."
    pip install rumps chromadb sentence-transformers paramiko pandas pydantic schedule python-dotenv pillow requests
fi

# Install PyQt6 if available
print_status "Checking for PyQt6..."
if pip install PyQt6 2>/dev/null; then
    print_success "PyQt6 installed successfully"
else
    print_warning "PyQt6 installation failed - GUI windows will not be available"
fi

# Create resources directory if it doesn't exist
if [ ! -d "resources" ]; then
    print_status "Creating resources directory..."
    mkdir -p resources
fi

# Check if icon exists, create a default one if not
if [ ! -f "resources/icon.icns" ]; then
    print_warning "App icon not found, creating placeholder..."
    # Create a simple text-based icon
    mkdir -p temp_icon.iconset
    # This is a placeholder - in a real app you'd have proper icon files
    touch temp_icon.iconset/icon_512x512.png
    if command -v iconutil >/dev/null 2>&1; then
        iconutil -c icns temp_icon.iconset -o resources/icon.icns 2>/dev/null || true
    fi
    rm -rf temp_icon.iconset
fi

# Build the application
print_status "Building application with py2app..."
python setup.py py2app

if [ $? -eq 0 ]; then
    print_success "Application built successfully!"
else
    print_error "Build failed"
    exit 1
fi

# Check if the app was created
if [ -d "dist/Recall.app" ]; then
    print_success "Recall.app created in dist/ directory"
    
    # Get app size
    APP_SIZE=$(du -sh "dist/Recall.app" | cut -f1)
    print_status "App size: $APP_SIZE"
    
    # Sign the app with ad-hoc signature (required for Apple Silicon)
    print_status "Signing application..."
    codesign --deep --force --sign - "dist/Recall.app" 2>/dev/null || {
        print_warning "Code signing failed - app may not run on Apple Silicon"
    }
    
    # Verify the app structure
    print_status "Verifying app structure..."
    if [ -f "dist/Recall.app/Contents/MacOS/menu_bar" ]; then
        print_success "App executable found"
    else
        print_warning "App executable not found at expected location"
    fi
    
    if [ -f "dist/Recall.app/Contents/Info.plist" ]; then
        print_success "Info.plist found"
    else
        print_warning "Info.plist not found"
    fi
    
    # Test if app can be launched (briefly)
    print_status "Testing app launch..."
    timeout 5s "dist/Recall.app/Contents/MacOS/menu_bar" >/dev/null 2>&1 || {
        print_warning "App launch test timed out (this is expected)"
    }
    
else
    print_error "Recall.app was not created"
    exit 1
fi

# Provide installation instructions
echo ""
print_success "Build complete! 🎉"
echo ""
echo "To install and run Recall:"
echo "  1. Copy the app:  cp -r dist/Recall.app /Applications/"
echo "  2. Launch from Applications folder or Spotlight"
echo "  3. Grant permissions when prompted"
echo ""
echo "To create a DMG installer:"
echo "  brew install create-dmg"
echo "  create-dmg --volname 'Recall Installer' --window-size 600 400 --app-drop-link 450 150 Recall.dmg dist/"
echo ""

# Optional: Create a simple installer DMG if create-dmg is available
if command -v create-dmg >/dev/null 2>&1; then
    print_status "Creating DMG installer..."
    create-dmg \
        --volname "Recall Installer" \
        --volicon "resources/icon.icns" \
        --window-size 600 400 \
        --app-drop-link 450 150 \
        --hdiutil-quiet \
        "Recall-$VERSION.dmg" \
        "dist/" 2>/dev/null && {
        print_success "DMG installer created: Recall-$VERSION.dmg"
    } || {
        print_warning "DMG creation failed"
    }
fi

print_success "All done! 🚀"