#!/bin/bash
# Agent-Core Installation Script
# Installs Agent-Core from PyPI or directly from source

set -e

VERSION="1.0.0"
REPO_URL="https://github.com/your-org/agent-core"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Agent-Core Installer v${VERSION}         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.8 or higher from https://www.python.org/downloads/"
        exit 1
    fi

    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Found Python $python_version"
}

install_from_pypi() {
    print_info "Installing Agent-Core from PyPI..."
    pip install --upgrade pip setuptools wheel
    pip install agent-core
    print_success "Agent-Core installed from PyPI"
}

install_from_source() {
    local repo_path="${1:-.}"

    print_info "Installing Agent-Core from source..."
    cd "$repo_path"
    pip install --upgrade pip setuptools wheel
    pip install -e .
    print_success "Agent-Core installed from source"
}

install_with_optional() {
    print_info "Installing Agent-Core with optional dependencies..."

    if [ "$1" = "redis" ]; then
        pip install agent-core[redis]
        print_success "Agent-Core with Redis support installed"
    elif [ "$1" = "dev" ]; then
        pip install agent-core[dev]
        print_success "Agent-Core with development tools installed"
    else
        pip install agent-core[dev,redis]
        print_success "Agent-Core with all optional dependencies installed"
    fi
}

verify_installation() {
    print_info "Verifying installation..."

    if python3 -c "import agent_core; print(f'Agent-Core {agent_core.__version__} installed')" 2>/dev/null; then
        print_success "Installation verified"
    else
        print_error "Installation verification failed"
        exit 1
    fi
}

show_next_steps() {
    echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Next Steps                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

    echo "1. Check version:"
    echo "   agent-core version\n"

    echo "2. Start the API server:"
    echo "   agent-core start --host 0.0.0.0 --port 8000\n"

    echo "3. Retrieve tools (in another terminal):"
    echo "   agent-core retrieve 'edit a file' --top-k 5\n"

    echo "4. Visit API docs:"
    echo "   http://localhost:8000/docs\n"

    echo "Documentation: $REPO_URL#readme"
}

main() {
    print_header

    # Parse arguments
    case "${1:-pypi}" in
        source)
            check_python
            install_from_source "${2:-.}"
            ;;
        redis)
            check_python
            install_from_pypi
            install_with_optional "redis"
            ;;
        dev)
            check_python
            install_from_pypi
            install_with_optional "dev"
            ;;
        all)
            check_python
            install_from_pypi
            install_with_optional "all"
            ;;
        *)
            check_python
            install_from_pypi
            ;;
    esac

    verify_installation
    show_next_steps

    echo -e "\n${GREEN}Installation complete!${NC}\n"
}

# Run main
main "$@"
