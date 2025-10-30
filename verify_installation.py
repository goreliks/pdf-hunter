#!/usr/bin/env python3
"""
PDF Hunter Installation Verification Script

This script verifies that all required dependencies and system libraries
are correctly installed for PDF Hunter.

Usage:
    uv run python verify_installation.py
"""

import sys
import subprocess
import importlib
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"⚠️  {text}")


def check_python_version():
    """Check if Python version is 3.11.x"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python version: {version_str}")
    
    if version.major == 3 and version.minor == 11:
        print_success(f"Python {version_str} is supported")
        return True
    else:
        print_error(f"Python {version_str} is not supported. Requires Python 3.11.x")
        return False


def check_module(module_name, display_name=None):
    """Check if a Python module can be imported."""
    if display_name is None:
        display_name = module_name
    
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print_success(f"{display_name} installed (version: {version})")
        return True
    except ImportError as e:
        print_error(f"{display_name} NOT installed: {e}")
        return False


def check_system_library(command, library_name):
    """Check if a system library is installed."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print_success(f"{library_name} installed")
            return True
        else:
            print_error(f"{library_name} NOT installed")
            return False
    except FileNotFoundError:
        print_error(f"{library_name} NOT installed (command not found)")
        return False


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print_header("Checking Playwright Browsers")
    
    try:
        result = subprocess.run(
            ["npx", "playwright", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Playwright installed: {version}")
            
            # Check if chromium is installed
            result = subprocess.run(
                ["npx", "playwright", "install", "--dry-run", "chromium"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if "is already installed" in result.stdout or result.returncode == 0:
                print_success("Chromium browser installed")
                return True
            else:
                print_warning("Chromium browser may not be installed")
                print("Run: npx playwright install chromium")
                return False
        else:
            print_error("Playwright NOT installed")
            print("Run: npm install")
            return False
            
    except FileNotFoundError:
        print_error("Node.js/npm NOT found")
        print("Install Node.js from: https://nodejs.org/")
        return False


def check_core_dependencies():
    """Check core Python dependencies."""
    print_header("Checking Core Python Dependencies")
    
    dependencies = [
        ('langchain', 'LangChain'),
        ('langgraph', 'LangGraph'),
        ('openai', 'OpenAI Python SDK'),
        ('pydantic', 'Pydantic'),
        ('loguru', 'Loguru'),
    ]
    
    results = []
    for module_name, display_name in dependencies:
        results.append(check_module(module_name, display_name))
    
    return all(results)


def check_pdf_dependencies():
    """Check PDF processing dependencies."""
    print_header("Checking PDF Processing Dependencies")

    dependencies = [
        ('pymupdf', 'PyMuPDF'),
        ('PIL', 'Pillow'),
        ('pdfid', 'PDFiD'),
    ]

    results = []
    for module_name, display_name in dependencies:
        results.append(check_module(module_name, display_name))

    # Check peepdf-3 separately (needs binary verification)
    print("\nChecking peepdf-3 (requires binary accessibility)...")
    peepdf_ok = False

    # Try via uv run (preferred - uses venv)
    try:
        result = subprocess.run(
            ["uv", "run", "peepdf", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        if result.returncode == 0 and "5.1.1" in result.stdout:
            print_success("peepdf-3 v5.1.1 accessible via uv run (venv)")
            peepdf_ok = True
        else:
            # Try checking if module exists
            try:
                import peepdf
                print_warning("peepdf module found but binary not accessible via uv run")
                print("  Try: uv pip install peepdf-3==5.1.1")
            except ImportError:
                pass
    except Exception:
        pass

    # Fallback: check system installation
    if not peepdf_ok:
        try:
            result = subprocess.run(
                ["peepdf", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            if result.returncode == 0:
                print_warning("peepdf found in system PATH (not in venv)")
                print("  For best reproducibility, install in venv:")
                print("  uv pip install peepdf-3==5.1.1")
                peepdf_ok = True
        except Exception:
            pass

    if not peepdf_ok:
        print_error("peepdf-3 NOT accessible")
        print("  Install: uv pip install peepdf-3==5.1.1")
        results.append(False)
    else:
        results.append(True)

    # Verify stpyv8 is NOT installed (we don't need it)
    print("\nVerifying stpyv8 is NOT installed...")
    try:
        import stpyv8
        print_warning("stpyv8 is installed (not needed and can cause issues)")
        print("  PDF Hunter doesn't require stpyv8")
        print("  Consider: uv pip uninstall stpyv8")
    except ImportError:
        print_success("stpyv8 correctly NOT installed")

    return all(results)


def check_vision_dependencies():
    """Check computer vision dependencies."""
    print_header("Checking Computer Vision Dependencies")
    
    # Check OpenCV
    opencv_ok = check_module('cv2', 'OpenCV')
    
    # Check pyzbar (depends on system zbar library)
    print("\nChecking pyzbar (requires system zbar library)...")
    try:
        import pyzbar
        from pyzbar import pyzbar as pyz
        print_success(f"pyzbar installed (version: {pyzbar.__version__})")
        
        # Try to use pyzbar to verify zbar library is accessible
        try:
            # This will fail if zbar library is not installed
            _ = pyz.ZBarSymbol
            print_success("zbar system library is accessible")
            zbar_ok = True
        except Exception as e:
            print_error(f"zbar system library NOT accessible: {e}")
            print("Install zbar:")
            print("  macOS: brew install zbar")
            print("  Ubuntu/Debian: sudo apt-get install libzbar0 libzbar-dev")
            print("  RHEL/CentOS: sudo dnf install zbar zbar-devel")
            zbar_ok = False
    except ImportError as e:
        print_error(f"pyzbar NOT installed: {e}")
        zbar_ok = False
    
    # Check imagehash
    imagehash_ok = check_module('imagehash', 'ImageHash')
    
    return opencv_ok and zbar_ok and imagehash_ok


def check_mcp_dependencies():
    """Check MCP (Model Context Protocol) dependencies."""
    print_header("Checking MCP Dependencies")

    results = []

    # Check Python MCP adapter
    mcp_ok = check_module('langchain_mcp_adapters', 'LangChain MCP Adapters')
    results.append(mcp_ok)

    # Check @playwright/mcp in root node_modules
    print("\nChecking @playwright/mcp (Node.js package)...")
    mcp_path = Path("node_modules/@playwright/mcp/package.json")
    if mcp_path.exists():
        try:
            import json
            with open(mcp_path) as f:
                data = json.load(f)
                version = data.get("version", "unknown")
                print_success(f"@playwright/mcp v{version} installed")

            # Verify binary works
            try:
                result = subprocess.run(
                    ["npx", "mcp-server-playwright", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                if result.returncode == 0:
                    print_success("mcp-server-playwright binary working")
                    results.append(True)
                else:
                    print_warning("mcp-server-playwright binary not executable")
                    results.append(False)
            except Exception:
                print_warning("Could not verify mcp-server-playwright binary")
                results.append(False)
        except Exception as e:
            print_error(f"Error checking @playwright/mcp: {e}")
            results.append(False)
    else:
        print_error("@playwright/mcp NOT installed in node_modules")
        print("  Run: npm install")
        results.append(False)

    return all(results)


def check_api_dependencies():
    """Check API server dependencies (optional)."""
    print_header("Checking API Server Dependencies (Optional)")
    
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('sse_starlette', 'SSE-Starlette'),
    ]
    
    results = []
    for module_name, display_name in dependencies:
        result = check_module(module_name, display_name)
        results.append(result)
        if not result:
            print(f"  To install: uv sync --group api")
    
    return all(results)


def check_environment_file():
    """Check if .env file exists."""
    print_header("Checking Environment Configuration")
    
    env_file = Path('.env')
    if env_file.exists():
        print_success(".env file exists")
        
        # Check for API keys (without revealing them)
        with open(env_file, 'r') as f:
            content = f.read()
            
        has_openai = 'OPENAI_API_KEY' in content and not content.split('OPENAI_API_KEY')[1].split('\n')[0].strip().endswith('=""')
        has_azure_key = 'AZURE_OPENAI_API_KEY' in content and not content.split('AZURE_OPENAI_API_KEY')[1].split('\n')[0].strip().endswith('=""')
        has_azure_endpoint = 'AZURE_OPENAI_ENDPOINT' in content
        has_azure_deployment = 'AZURE_OPENAI_DEPLOYMENT_NAME' in content and not content.split('AZURE_OPENAI_DEPLOYMENT_NAME')[1].split('\n')[0].strip().endswith('=""')
        
        if has_openai:
            print_success("OPENAI_API_KEY configured")
        
        if has_azure_key and has_azure_endpoint and has_azure_deployment:
            print_success("Azure OpenAI fully configured (key, endpoint, deployment)")
        elif has_azure_key or has_azure_endpoint or has_azure_deployment:
            print_warning("Azure OpenAI partially configured")
            if not has_azure_key:
                print("  Missing: AZURE_OPENAI_API_KEY")
            if not has_azure_endpoint:
                print("  Missing: AZURE_OPENAI_ENDPOINT")
            if not has_azure_deployment:
                print("  ⚠️  CRITICAL: Missing AZURE_OPENAI_DEPLOYMENT_NAME")
                print("     This will cause model initialization errors!")
        
        if not (has_openai or (has_azure_key and has_azure_endpoint and has_azure_deployment)):
            print_warning("No complete AI provider configuration found in .env")
            print("Configure either:")
            print("  OpenAI: OPENAI_API_KEY")
            print("  Azure OpenAI: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME")
        
        return True
    else:
        print_warning(".env file NOT found")
        print("Copy .env.example to .env and add your API keys")
        return False


def check_test_files():
    """Check if test PDF files exist."""
    print_header("Checking Test Files")
    
    test_files = [
        'tests/assets/pdfs/hello_qr_and_link.pdf',
        'tests/assets/pdfs/test_mal_one.pdf',
    ]
    
    results = []
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            print_success(f"{test_file} exists")
            results.append(True)
        else:
            print_warning(f"{test_file} NOT found")
            results.append(False)
    
    return all(results)


def check_frontend_dependencies():
    """Check frontend dependencies (optional)."""
    print_header("Checking Frontend Dependencies (Optional)")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print_warning("frontend directory NOT found")
        return False
    
    # Check if node_modules exists
    node_modules = frontend_dir / 'node_modules'
    if node_modules.exists():
        print_success("Frontend node_modules installed")
    else:
        print_warning("Frontend node_modules NOT found")
        print("  Run: cd frontend && npm install")
        return False
    
    # Check for package.json
    package_json = frontend_dir / 'package.json'
    if package_json.exists():
        print_success("Frontend package.json exists")
    else:
        print_error("Frontend package.json NOT found")
        return False
    
    # Check if Vite is available
    try:
        result = subprocess.run(
            ["npm", "run", "--prefix", "frontend", "build", "--", "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        if result.returncode == 0 or "vite" in result.stdout.lower():
            print_success("Vite build system available")
        else:
            print_warning("Vite may not be properly configured")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_warning("Could not verify Vite installation")
    
    return True


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("  PDF HUNTER INSTALLATION VERIFICATION")
    print("=" * 70)
    
    all_checks = []
    
    # Required checks
    all_checks.append(check_python_version())
    all_checks.append(check_core_dependencies())
    all_checks.append(check_pdf_dependencies())
    all_checks.append(check_vision_dependencies())
    all_checks.append(check_mcp_dependencies())
    all_checks.append(check_playwright_browsers())
    
    # Optional checks (don't fail on these)
    check_api_dependencies()
    check_environment_file()
    check_test_files()
    check_frontend_dependencies()
    
    # Summary
    print_header("Verification Summary")
    
    if all(all_checks):
        print_success("All required dependencies are installed!")
        print("\nYou can now run PDF Hunter:")
        print("  Backend CLI: uv run python -m pdf_hunter.orchestrator.graph --help")
        print("  Web API: uv run python -m pdf_hunter.api.server")
        print("  Frontend: cd frontend && npm run dev")
        print("  Docker: docker-compose up")
        return 0
    else:
        print_error("Some required dependencies are missing!")
        print("\nPlease install missing dependencies and run this script again.")
        print("\nFor detailed installation instructions, see:")
        print("  README.md or run: ./install.sh")
        return 1


if __name__ == '__main__':
    sys.exit(main())
