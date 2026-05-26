#!/bin/bash
#
# Rubik's Cube Solver - Application Launcher
#
# Purpose: Interactive menu to launch any of the three application interfaces
# Usage: ./run_app.sh
#
# Features:
# - Automatically creates and activates Python virtual environment
# - Installs all dependencies from requirements.txt
# - Provides menu to select which interface to run:
#   1. CLI - Command line interface with colored terminal output
#   2. Web - Flask server with 3D visualization (http://localhost:5001)
#   3. Desktop - PySide6/OpenGL desktop application
#   4. Tests - Run full test suite (28 unit tests)
#
# First-time setup: Just run this script, it handles everything!

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${BLUE}🎲 Rubik's Cube Solver - Application Launcher${NC}"
echo "================================================"

# Function to create and activate virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
    fi

    echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"

    # Install requirements
    pip install -r "$PROJECT_DIR/requirements.txt"
}

# Function to display menu
show_menu() {
    echo ""
    echo -e "${BLUE}Select interface to run:${NC}"
    echo "1) CLI - Command Line Interface"
    echo "2) Web - Flask Web Application (http://localhost:5001)"
    echo "3) Desktop - PySide6 Desktop Application (3D OpenGL)"
    echo "4) Tests - Run test suite"
    echo "5) Exit"
    echo ""
}

# Function to run CLI
run_cli() {
    echo -e "${GREEN}🖥️  Starting CLI interface...${NC}"
    cd "$PROJECT_DIR"
    python -m solver.cli
}

# Function to run Flask web app
run_web() {
    echo -e "${GREEN}🌐 Starting Flask web application...${NC}"
    echo -e "${YELLOW}Access the application at: http://localhost:5001${NC}"
    cd "$PROJECT_DIR"
    python -m solver.flask_app
}

# Function to run desktop app
run_desktop() {
    echo -e "${GREEN}🖼️  Starting PySide6 desktop application...${NC}"
    cd "$PROJECT_DIR"
    python -m solver.desktop_app
}

# Function to run tests
run_tests() {
    echo -e "${GREEN}🧪 Running test suite...${NC}"
    cd "$PROJECT_DIR"
    python -m pytest solver/ -v
}

# Main execution
main() {
    cd "$PROJECT_DIR"

    # Setup virtual environment and dependencies
    setup_venv

    # Main application loop
    while true; do
        show_menu
        read -p "Enter your choice (1-5): " choice

        case $choice in
            1)
                run_cli
                ;;
            2)
                run_web
                ;;
            3)
                run_desktop
                ;;
            4)
                run_tests
                ;;
            5)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please select 1-5.${NC}"
                ;;
        esac

        echo ""
        echo -e "${YELLOW}Press Enter to return to menu...${NC}"
        read
    done
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Run main function
main "$@"
