#!/bin/bash

# LEW Setup Script - Terminal-Agnostic Installation
# This script sets up LEW to work with any terminal (not just iTerm2)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LEW_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LEW_LOG_DIR="$HOME/lew_logs"
SHELL_RC_FILE=""

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

detect_shell() {
    if [[ -n "$ZSH_VERSION" ]]; then
        echo "zsh"
        SHELL_RC_FILE="$HOME/.zshrc"
    elif [[ -n "$BASH_VERSION" ]]; then
        echo "bash"
        SHELL_RC_FILE="$HOME/.bashrc"
    else
        # Try to detect from $SHELL
        case "$SHELL" in
            */zsh)
                echo "zsh"
                SHELL_RC_FILE="$HOME/.zshrc"
                ;;
            */bash)
                echo "bash"
                SHELL_RC_FILE="$HOME/.bashrc"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    fi
}

check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed."
        exit 1
    fi
    
    # Check script command (for output capture)
    if ! command -v script &> /dev/null; then
        print_warning "The 'script' command is not available. Some features may be limited."
    fi
    
    print_success "All dependencies are available."
}

install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [[ -f "$LEW_DIR/requirements.txt" ]]; then
        pip3 install -r "$LEW_DIR/requirements.txt"
        print_success "Python dependencies installed."
    else
        print_warning "requirements.txt not found. Installing individual packages..."
        pip3 install httpx python-dotenv
    fi
}

setup_environment() {
    print_status "Setting up environment..."
    
    # Create log directory
    mkdir -p "$LEW_LOG_DIR"
    print_success "Created log directory: $LEW_LOG_DIR"
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$LEW_DIR/.env" ]]; then
        if [[ -f "$LEW_DIR/.env.sample" ]]; then
            cp "$LEW_DIR/.env.sample" "$LEW_DIR/.env"
            print_success "Created .env file from template."
        else
            # Create basic .env file
            cat > "$LEW_DIR/.env" << EOF
# LEW Configuration
OPENAI_API_KEY=your_openai_api_key_here
LEW_LOG_DIR=$LEW_LOG_DIR

# Legacy iTerm2 settings (optional, for fallback)
ITERM2_LOGS=
CLI_LOG_DELIMITER=
EOF
            print_success "Created basic .env file."
        fi
        
        print_warning "Please edit $LEW_DIR/.env and add your OpenAI API key."
    else
        print_success ".env file already exists."
    fi
}

setup_shell_integration() {
    local shell_type=$(detect_shell)
    
    print_status "Setting up shell integration for $shell_type..."
    
    if [[ "$shell_type" == "unknown" ]]; then
        print_error "Unknown shell type. Please manually add the following to your shell configuration:"
        echo "    source $LEW_DIR/app/shell_integration.sh"
        return 1
    fi
    
    # Check if integration is already set up
    if grep -q "LEW shell integration" "$SHELL_RC_FILE" 2>/dev/null; then
        print_success "Shell integration already configured."
        return 0
    fi
    
    # Add integration to shell rc file
    echo "" >> "$SHELL_RC_FILE"
    echo "# LEW shell integration" >> "$SHELL_RC_FILE"
    echo "export LEW_LOG_DIR=\"$LEW_LOG_DIR\"" >> "$SHELL_RC_FILE"
    echo "export LEW_APP_DIR=\"$LEW_DIR/app\"" >> "$SHELL_RC_FILE"
    echo "source \"$LEW_DIR/app/shell_integration.sh\"" >> "$SHELL_RC_FILE"
    
    print_success "Shell integration added to $SHELL_RC_FILE"
}

create_lew_alias() {
    print_status "Creating LEW alias..."
    
    # The alias is already created in shell_integration.sh
    # But let's add a direct alias as well for convenience
    local shell_type=$(detect_shell)
    
    if [[ "$shell_type" != "unknown" ]]; then
        if ! grep -q "alias lew=" "$SHELL_RC_FILE" 2>/dev/null; then
            echo "alias lew='python3 $LEW_DIR/app/command.py'" >> "$SHELL_RC_FILE"
            print_success "LEW alias added to $SHELL_RC_FILE"
        fi
    fi
}

test_setup() {
    print_status "Testing setup..."
    
    # Test if Python modules can be imported
    if python3 -c "import sys; sys.path.insert(0, '$LEW_DIR/app'); from terminal_logger import TerminalLogger; print('Terminal logger import successful')" 2>/dev/null; then
        print_success "Terminal logger module is working."
    else
        print_error "Terminal logger module is not working properly."
        return 1
    fi
    
    # Test if .env file has API key
    if [[ -f "$LEW_DIR/.env" ]]; then
        if grep -q "OPENAI_API_KEY=your_openai_api_key_here" "$LEW_DIR/.env" || grep -q "OPENAI_API_KEY=$" "$LEW_DIR/.env"; then
            print_warning "OpenAI API key is not set in .env file."
        else
            print_success "OpenAI API key is configured."
        fi
    fi
    
    print_success "Setup test completed."
}

main() {
    echo "======================================"
    echo "LEW Terminal-Agnostic Setup Script"
    echo "======================================"
    echo ""
    
    print_status "Starting LEW setup..."
    
    check_dependencies
    install_python_dependencies
    setup_environment
    setup_shell_integration
    create_lew_alias
    test_setup
    
    echo ""
    echo "======================================"
    print_success "LEW setup completed successfully!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Edit $LEW_DIR/.env and add your OpenAI API key"
    echo "2. Restart your terminal or run: source $SHELL_RC_FILE"
    echo "3. Test LEW by running a command and then typing: lew"
    echo ""
    echo "LEW now works with any terminal (not just iTerm2)!"
    echo "It will work in VSCode, Cursor, and any other terminal."
}

# Run the main function
main "$@"