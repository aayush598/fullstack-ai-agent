#!/bin/bash

# Autonomous Full-Stack Application Factory - Quick Start Script
# This script automates the setup process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  Autonomous Full-Stack Application Factory Setup        ║"
    echo "║  Version 1.0.0                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
        print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    print_step "Python version: $PYTHON_VERSION ✓"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    print_step "pip3 installed ✓"
    
    # Check git
    if ! command -v git &> /dev/null; then
        print_warning "git is not installed (optional but recommended)"
    else
        print_step "git installed ✓"
    fi
}

setup_virtual_environment() {
    print_step "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_step "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_step "Virtual environment activated"
}

install_dependencies() {
    print_step "Installing dependencies..."
    
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    
    print_step "Dependencies installed ✓"
}

setup_environment() {
    print_step "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_step ".env file created"
        
        echo ""
        echo -e "${YELLOW}IMPORTANT: Please edit .env file and add your API keys:${NC}"
        echo "  - ANTHROPIC_API_KEY"
        echo "  - OPENAI_API_KEY"
        echo ""
        
        read -p "Press Enter to open .env in your default editor..."
        ${EDITOR:-nano} .env
    else
        print_warning ".env file already exists"
    fi
}

initialize_system() {
    print_step "Initializing system..."
    
    # Create directories
    python3 << EOF
from fullstack_agent_main import SystemConfig
SystemConfig.setup_directories()
print("✓ Directories created")
EOF
    
    print_step "System initialized ✓"
}

run_tests() {
    print_step "Running tests (optional)..."
    
    read -p "Do you want to run tests? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pytest tests/ -v
        print_step "Tests completed"
    else
        print_warning "Tests skipped"
    fi
}

print_next_steps() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Setup Complete! 🎉                                     ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate virtual environment (if not already active):"
    echo -e "   ${BLUE}source venv/bin/activate${NC}"
    echo ""
    echo "2. Start the Streamlit UI:"
    echo -e "   ${BLUE}streamlit run streamlit_ui.py${NC}"
    echo ""
    echo "   Or start the FastAPI server:"
    echo -e "   ${BLUE}python agno_os_server.py${NC}"
    echo ""
    echo "3. Access the application:"
    echo -e "   Streamlit UI: ${BLUE}http://localhost:8501${NC}"
    echo -e "   FastAPI:      ${BLUE}http://localhost:8000${NC}"
    echo -e "   API Docs:     ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
    echo "4. Generate your first application!"
    echo ""
    echo "For more information, see:"
    echo "  - README.md - Complete documentation"
    echo "  - DEPLOYMENT.md - Production deployment guide"
    echo ""
}

# Main execution
main() {
    print_header
    
    check_requirements
    setup_virtual_environment
    install_dependencies
    setup_environment
    initialize_system
    run_tests
    print_next_steps
}

# Run main function
main