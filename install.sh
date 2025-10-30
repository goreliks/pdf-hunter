#!/bin/bash
# PDF Hunter Full Stack Installation Script for macOS/Linux
# Installs both backend (Python/LangGraph) and frontend (React/Vite)

set -e  # Exit on error

echo "=========================================="
echo "PDF Hunter Full Stack Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "ℹ $1"
}

# Step 1: Check Python version
echo "Step 1/6: Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" = "3" ] && [ "$PYTHON_MINOR" = "11" ]; then
        PYTHON_CMD="python3"
    else
        print_error "Python 3.11.x required, but found Python $PYTHON_VERSION"
        print_info "Please install Python 3.11 using:"
        print_info "  macOS: brew install python@3.11"
        print_info "  Ubuntu/Debian: sudo apt install python3.11"
        print_info "  or use pyenv: pyenv install 3.11"
        exit 1
    fi
else
    print_error "Python 3 not found"
    print_info "Please install Python 3.11 first"
    exit 1
fi
print_success "Python 3.11 found: $PYTHON_CMD"
echo ""

# Step 2: Install system dependencies for OpenCV and zbar
echo "Step 2/6: Installing system dependencies..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v apt-get &> /dev/null; then
        echo "Installing OpenCV and zbar system libraries..."
        # Use sudo only if not running as root
        if [ "$EUID" -ne 0 ]; then
            SUDO_CMD="sudo"
        else
            SUDO_CMD=""
        fi
        
        # Install OpenCV dependencies (libGL for cv2)
        $SUDO_CMD apt-get update -qq > /dev/null 2>&1
        $SUDO_CMD apt-get install -y -qq libgl1-mesa-glx libglib2.0-0 > /dev/null 2>&1
        
        # Install zbar library
        $SUDO_CMD apt-get install -y -qq libzbar0 libzbar-dev > /dev/null 2>&1
        
        print_success "System dependencies installed (OpenCV, zbar)"
    else
        print_warning "apt-get not found, skipping system dependencies"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &> /dev/null; then
        echo "Installing zbar via Homebrew..."
        brew install zbar > /dev/null 2>&1
        print_success "System dependencies installed (zbar)"
    else
        print_warning "Homebrew not found, skipping zbar installation"
    fi
else
    print_warning "Unknown OS, skipping system dependencies"
fi
echo ""

# Step 3: Check/Install zbar (deprecated - now handled in Step 2)
echo "Step 3/6: Verifying zbar library..."
if $PYTHON_CMD -c "import pyzbar" 2>/dev/null; then
    print_success "zbar already accessible"
else
    print_warning "zbar library not found - QR code detection may not work"
    print_info "  System library should have been installed in Step 2"
    print_info "  Python package will be installed in Step 4"
fi
echo ""

# Step 4: Install uv if not present
echo "Step 4/7: Checking for uv package manager..."
if ! command -v uv &> /dev/null; then
    print_warning "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    # Also add uv's local bin directory
    export PATH="$HOME/.local/bin:$PATH"
    print_success "uv installed"
else
    print_success "uv found"
fi
echo ""

# Step 5: Install Python dependencies
echo "Step 5/7: Installing Python dependencies..."
echo "Installing Python packages with dev and api groups..."
# Ensure uv is in PATH (it may have just been installed)
export PATH="$HOME/.local/bin:$PATH"
uv sync --group dev --group api
print_success "Python packages installed"

# Install peepdf-3 (installs with deps, then removes problematic stpyv8)
echo "Installing peepdf-3..."
uv pip install peepdf-3==5.1.1

# Remove stpyv8 if it was installed (optional dependency we don't need)
if uv pip show stpyv8 > /dev/null 2>&1; then
    echo "Removing stpyv8 (not needed for PDF Hunter)..."
    uv pip uninstall stpyv8 --yes 2>/dev/null || true
fi

# Verify peepdf binary is accessible
if uv run peepdf --version > /dev/null 2>&1; then
    print_success "peepdf-3 installed and verified"
else
    print_error "peepdf-3 installation failed or binary not accessible"
    print_info "Checking for system peepdf as fallback..."
    if command -v peepdf &> /dev/null; then
        print_warning "System peepdf found (will be used as fallback)"
    else
        print_error "peepdf not accessible"
        exit 1
    fi
fi
echo ""

# Step 6: Install Node.js dependencies
echo "Step 6/7: Installing Node.js dependencies..."

# Check if Node.js is installed and if version is >= 18
NODE_VERSION=""
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
fi

if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" -lt 18 ]; then
    if [ -n "$NODE_VERSION" ]; then
        print_warning "Node.js v$NODE_VERSION found, but v18+ is required. Upgrading..."
    else
        print_warning "Node.js not found, installing..."
    fi
    
    # Install Node.js 20.x (LTS) from NodeSource
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing Node.js 20.x LTS from NodeSource..."
        # Download and run NodeSource setup script
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - > /dev/null 2>&1
        sudo apt-get install -y -qq nodejs > /dev/null 2>&1
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install node@20
        else
            print_error "Homebrew not found. Please install Node.js 18+ manually from https://nodejs.org/"
            exit 1
        fi
    else
        print_error "Unsupported OS. Please install Node.js 18+ manually from https://nodejs.org/"
        exit 1
    fi
    
    print_success "Node.js installed: $(node --version)"
else
    if [ "$NODE_VERSION" -ge 20 ]; then
        print_success "Node.js found: v$NODE_VERSION (recommended v20+ LTS)"
    else
        print_success "Node.js found: v$NODE_VERSION"
        print_info "Note: v20+ LTS recommended for best compatibility (current v$NODE_VERSION will work)"
    fi
fi

npm install
print_success "Node.js packages installed"

# Verify @playwright/mcp was installed
if [ -d "node_modules/@playwright/mcp" ]; then
    print_success "@playwright/mcp installed"
else
    print_error "@playwright/mcp NOT found in node_modules"
    print_info "This is required for URL investigation via MCP"
    exit 1
fi
echo ""

# Step 7: Install Playwright browsers
echo "Step 7/7: Installing Playwright browsers..."
npx playwright install chromium
print_success "Playwright browsers installed"
echo ""

# Final verification
echo "=========================================="
echo "Running installation verification..."
echo "=========================================="
echo ""
uv run python verify_installation.py

echo ""
echo "=========================================="
echo "Installing Frontend Dependencies..."
echo "=========================================="
echo ""

# Step 7: Install frontend dependencies
echo "Step 7/8: Installing frontend (React/Vite)..."
if [ ! -d "frontend" ]; then
    print_error "Frontend directory not found"
    exit 1
fi

cd frontend
npm install
print_success "Frontend dependencies installed"
cd ..
echo ""

# Step 8: Optional - Build frontend for production
read -p "Build frontend for production? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building frontend..."
    cd frontend
    npm run build
    print_success "Frontend built successfully (output in frontend/dist/)"
    cd ..
else
    print_info "Skipping frontend build (you can build later with: cd frontend && npm run build)"
fi
echo ""

echo ""
echo "=========================================="
print_success "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your .env file:"
echo "   cp .env.example .env"
echo "   # Edit .env and add your API keys:"
echo ""
echo "   For OpenAI:"
echo "     OPENAI_API_KEY=your_key_here"
echo ""
echo "   For Azure OpenAI (recommended for production):"
echo "     AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/"
echo "     AZURE_OPENAI_API_KEY=your_azure_key_here"
echo "     AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name"
echo "     AZURE_OPENAI_API_VERSION=2024-12-01-preview"
echo ""
echo "2. Start the application:"
echo "   # Option A: Development mode (separate terminals)"
echo "   # Terminal 1 - Start backend:"
echo "   uv run python -m pdf_hunter.api.server"
echo ""
echo "   # Terminal 2 - Start frontend:"
echo "   cd frontend && npm run dev"
echo "   # Access at: http://localhost:5173"
echo ""
echo "   # Option B: Docker (recommended for production):"
echo "   docker-compose up"
echo "   # Access at: http://localhost"
echo ""
echo "3. Web Dashboard Features:"
echo "   - Upload PDFs for analysis"
echo "   - Real-time streaming logs"
echo "   - Toggle Dev Mode for frontend development (no backend needed)"
echo ""
