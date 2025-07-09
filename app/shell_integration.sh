#!/bin/bash

# LEW Shell Integration - Universal Terminal Logging
# This script provides command capture for both ZSH and Bash

# Configuration
LEW_LOG_DIR="${LEW_LOG_DIR:-$HOME/lew_logs}"
LEW_APP_DIR="${LEW_APP_DIR:-$(dirname "${BASH_SOURCE[0]}")}"
LEW_PYTHON_LOGGER="$LEW_APP_DIR/terminal_logger.py"
LEW_TEMP_OUTPUT="$LEW_LOG_DIR/.temp_output"
LEW_LAST_COMMAND="$LEW_LOG_DIR/.last_command"

# Create log directory if it doesn't exist
mkdir -p "$LEW_LOG_DIR"

# Function to clean and log command output
lew_log_command() {
    local command="$1"
    local output="$2"
    local exit_code="${3:-0}"
    
    # Only log if we have both command and logger
    if [[ -n "$command" && -f "$LEW_PYTHON_LOGGER" ]]; then
        python3 "$LEW_PYTHON_LOGGER" log_entry "$command" "$output" "$exit_code" 2>/dev/null
    fi
}

# Function to capture command output using script
lew_capture_output() {
    local command="$1"
    local temp_file="$LEW_TEMP_OUTPUT"
    
    # Use script to capture terminal output
    if command -v script >/dev/null 2>&1; then
        # Linux version of script
        if script --version 2>&1 | grep -q "util-linux"; then
            script -q -c "$command" "$temp_file" 2>/dev/null
        # macOS version of script
        else
            script -q "$temp_file" bash -c "$command" 2>/dev/null
        fi
    else
        # Fallback: direct execution
        eval "$command" > "$temp_file" 2>&1
    fi
    
    # Return the output
    cat "$temp_file" 2>/dev/null
    rm -f "$temp_file" 2>/dev/null
}

# ZSH-specific functions
if [[ -n "$ZSH_VERSION" ]]; then
    # ZSH hooks
    autoload -U add-zsh-hook
    
    # Before command execution
    lew_preexec() {
        LEW_CURRENT_COMMAND="$1"
        LEW_COMMAND_START_TIME=$(date +%s)
        echo "$LEW_CURRENT_COMMAND" > "$LEW_LAST_COMMAND"
    }
    
    # After command execution
    lew_precmd() {
        local exit_code=$?
        
        if [[ -n "$LEW_CURRENT_COMMAND" ]]; then
            # Try to get command output from history
            # This is a simplified approach - in practice, capturing output
            # during execution is complex, so we'll use the Python logger
            # to re-execute safe commands for output
            
            # For now, just log the command without output
            # The Python script will handle output capture when needed
            if [[ -f "$LEW_PYTHON_LOGGER" ]]; then
                python3 -c "
import sys
sys.path.insert(0, '$LEW_APP_DIR')
from terminal_logger import TerminalLogger
logger = TerminalLogger('$LEW_LOG_DIR')
logger.log_command('$LEW_CURRENT_COMMAND', '', $exit_code)
" 2>/dev/null
            fi
        fi
        
        unset LEW_CURRENT_COMMAND
        unset LEW_COMMAND_START_TIME
    }
    
    # Register hooks
    add-zsh-hook preexec lew_preexec
    add-zsh-hook precmd lew_precmd

# Bash-specific functions
elif [[ -n "$BASH_VERSION" ]]; then
    # Bash hooks using DEBUG trap and PROMPT_COMMAND
    
    lew_debug_trap() {
        # Only capture interactive commands
        if [[ "$BASH_COMMAND" != "lew_prompt_command" && "$BASH_COMMAND" != lew_* ]]; then
            LEW_CURRENT_COMMAND="$BASH_COMMAND"
            echo "$LEW_CURRENT_COMMAND" > "$LEW_LAST_COMMAND"
        fi
    }
    
    lew_prompt_command() {
        local exit_code=$?
        
        if [[ -n "$LEW_CURRENT_COMMAND" ]]; then
            # Log the command
            if [[ -f "$LEW_PYTHON_LOGGER" ]]; then
                python3 -c "
import sys
sys.path.insert(0, '$LEW_APP_DIR')
from terminal_logger import TerminalLogger
logger = TerminalLogger('$LEW_LOG_DIR')
logger.log_command('$LEW_CURRENT_COMMAND', '', $exit_code)
" 2>/dev/null
            fi
        fi
        
        unset LEW_CURRENT_COMMAND
    }
    
    # Set up traps
    trap 'lew_debug_trap' DEBUG
    PROMPT_COMMAND="lew_prompt_command${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
fi

# Function to manually log a command with output (for testing)
lew_manual_log() {
    local command="$1"
    if [[ -n "$command" ]]; then
        local output=$(eval "$command" 2>&1)
        local exit_code=$?
        lew_log_command "$command" "$output" "$exit_code"
        echo "$output"
    fi
}

# Enhanced LEW command that works with the new logging system
lew_enhanced() {
    local message=""
    local count=1
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --cnt)
                count="$2"
                shift 2
                ;;
            *)
                message="$1"
                shift
                ;;
        esac
    done
    
    # Call the original LEW command with the new logging system
    python3 "$LEW_APP_DIR/command.py" "$message" --cnt "$count"
}

# Create alias for enhanced LEW
alias lew='lew_enhanced'

echo "LEW shell integration loaded for $([[ -n "$ZSH_VERSION" ]] && echo "ZSH" || echo "Bash")"