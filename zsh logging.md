# Attempting logging natively in ZSH

I fought long and hard trying to log the output from commands natively in ZSH, GPT and Google were helpful but couldn't get it to a satisfactory spot. Below is my last attempt, if you have any insights please do share!

The challenge I have with the following is the formatting of the logs, sometimes extraneous ASCII characeters were being loggs, and the same command and/or output were logged a dozen times, making parsing a nightmare.

```bash
# Path to the command log
COMMAND_LOG="$HOME/.command_log"
# Temporary file for capturing command output
TEMP_OUTPUT_FILE="$HOME/.last_command_output"

# Clear the command log at the start of the session
: > "$COMMAND_LOG"

# Function to trim the command log to the last 10 commands
trim_command_log() {
    # Split the log file into commands, keep the last 10 commands, and join them back together
    tail -r "$COMMAND_LOG" | awk -v RS="New Command" -v ORS="New Command" 'NR <= 10' | tail -r > "$COMMAND_LOG.tmp"
    # Replace the original log file with the trimmed version
    mv "$COMMAND_LOG.tmp" "$COMMAND_LOG"
}

# Custom hook function to execute before any command
preexec() {
    # Log the command
    echo "-----New Command-----" >> "$COMMAND_LOG"
    echo "Command: $1" >> "$COMMAND_LOG"
    if [[ "$1" != sudo* ]]; then
        # Prepare to capture the command's output if not starting with 'sudo'
        exec > >(tee -a "$TEMP_OUTPUT_FILE") 2>&1
    fi
}

# Custom hook function to execute after any command
precmd() {
    # Reset output redirection to the default for the next command
    exec >&1 2>&1
    # Append the output from the last command to the log, filtering out control sequences
    if [[ -s "$TEMP_OUTPUT_FILE" ]]; then
        echo "Output:" >> "$COMMAND_LOG"
        # Use sed to filter out ANSI escape sequences
        # tr -d '\000' <"$TEMP_OUTPUT_FILE" >> "$COMMAND_LOG"
        sed -E 's/\x1b\[[0-9;]*[mGKH]|\x1b\]0;[^\x07]*\x07|\x1b[[][?][0-9;]*[hl]//g' "$TEMP_OUTPUT_FILE" >> "$COMMAND_LOG"
        : > "$TEMP_OUTPUT_FILE" # Clear temporary file for the next command
    fi
    # Trim the command log to the last 10 commands
    trim_command_log
}
```
