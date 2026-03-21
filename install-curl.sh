#!/bin/bash
# Agent-Core Quick Install via curl
# Usage: curl -fsSL https://raw.githubusercontent.com/your-org/agent-core/main/install-curl.sh | bash

set -e

VERSION="1.0.0"
REPO_URL="https://github.com/your-org/agent-core"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Agent-Core Quick Install v${VERSION}     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

main() {
    print_header

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        echo "Install from: https://www.python.org/downloads/"
        exit 1
    fi

    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Found Python $python_version"

    # Install
    print_info "Installing Agent-Core..."
    pip install --upgrade pip setuptools wheel
    pip install agent-core

    # Verify
    print_info "Verifying installation..."
    if python3 -c "import agent_core; print(f'Agent-Core {agent_core.__version__} installed')" 2>/dev/null; then
        print_success "Installation verified"
    else
        print_error "Installation verification failed"
        exit 1
    fi

    # Next steps
    echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Next Steps                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

    echo "1. Start the API server:"
    echo "   ${YELLOW}agent-core start${NC}\n"

    echo "2. Retrieve tools (in another terminal):"
    echo "   ${YELLOW}agent-core retrieve 'edit a file'${NC}\n"

    echo "3. Visit API docs:"
    echo "   ${BLUE}http://localhost:8000/docs${NC}\n"

    echo "Documentation: $REPO_URL"
    echo -e "\n${GREEN}Ready to use!${NC}\n"
}

main "$@"
