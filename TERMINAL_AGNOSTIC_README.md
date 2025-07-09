# LEW - Terminal-Agnostic Version

This version of LEW (LLM Enhanced Workflow) has been enhanced to work with **any terminal**, not just iTerm2. It now works seamlessly in VSCode, Cursor, standard terminal emulators, and any other terminal environment.

## 🎯 Key Improvements

- **Universal Terminal Support**: Works with any terminal (Bash, ZSH, VSCode, Cursor, etc.)
- **No iTerm2 Dependency**: Completely removed the requirement for iTerm2
- **Enhanced Command Capture**: Better handling of ANSI escape sequences and output formatting
- **Cross-Platform**: Works on both Mac and Linux
- **Improved Reliability**: More robust parsing and fewer edge cases

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

The setup script will:
- Install Python dependencies
- Create necessary directories
- Set up shell integration
- Configure environment variables
- Add LEW alias to your shell

### Option 2: Manual Setup

1. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Create `.env` file**:
   ```bash
   cp .env.sample .env
   # Edit .env and add your OpenAI API key
   ```

3. **Add to your shell configuration** (`.bashrc` or `.zshrc`):
   ```bash
   # LEW shell integration
   export LEW_LOG_DIR="$HOME/lew_logs"
   export LEW_APP_DIR="/path/to/lew-llm-cli/app"
   source "/path/to/lew-llm-cli/app/shell_integration.sh"
   ```

4. **Restart your terminal** or run:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

## 📚 How It Works

### Command Capture System

The new system uses shell hooks to capture commands and their context:

1. **Shell Integration**: Uses `preexec`/`precmd` hooks in ZSH and `DEBUG` trap in Bash
2. **Command Logging**: Stores commands in JSON format with timestamps
3. **Output Handling**: Captures output for safe-to-rerun commands
4. **ANSI Cleaning**: Removes terminal escape sequences for clean parsing

### File Structure

```
~/lew_logs/
├── session_1234567890.json    # Command logs from current session
├── session_1234567891.json    # Command logs from previous session
└── .temp_output               # Temporary output capture file
```

### Log Format

Each command is stored as a JSON entry:
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "command": "git status",
  "output": "On branch main\nnothing to commit...",
  "exit_code": 0
}
```

## 🎮 Usage

### Basic Usage

```bash
# After running a command, get help
$ git status
fatal: not a git repository
$ lew

# With a custom message
$ lew "help me fix this git issue"

# Include multiple commands
$ lew --cnt 3

# Chat without sending command history
$ lew "how do I list files?" --cnt 0
```

### Advanced Features

- **Safe Command Re-execution**: For read-only commands, LEW will re-run them to get fresh output
- **ANSI Sequence Handling**: Properly cleans terminal colors and formatting
- **Multi-session Support**: Reads commands from multiple terminal sessions
- **Automatic Cleanup**: Removes log files older than 7 days

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
LEW_LOG_DIR=/custom/log/directory    # Default: ~/lew_logs

# Legacy iTerm2 fallback (optional)
ITERM2_LOGS=/path/to/iterm2/logs/*
CLI_LOG_DELIMITER=username@hostname
```

### Shell Configuration

The shell integration automatically detects your shell (ZSH or Bash) and configures appropriate hooks. You can customize the behavior by modifying variables in your shell configuration:

```bash
# Custom log directory
export LEW_LOG_DIR="$HOME/custom_lew_logs"

# Custom app directory
export LEW_APP_DIR="/path/to/lew/app"
```

## 🧪 Testing

### Test the Setup

1. **Check if integration is working**:
   ```bash
   # Run a command
   ls -la
   
   # Check if it was logged
   cat ~/lew_logs/session_*.json | tail -1
   ```

2. **Test LEW functionality**:
   ```bash
   # Generate an error
   git status
   
   # Ask LEW for help
   lew
   ```

3. **Test with different terminals**:
   - Standard terminal
   - VSCode integrated terminal
   - Cursor terminal
   - SSH sessions

### Manual Testing

You can manually test the terminal logger:

```bash
# Test command logging
python3 app/terminal_logger.py log_entry "test command" "test output" 0

# Test command execution with capture
python3 app/terminal_logger.py ls -la
```

## 🔍 Troubleshooting

### Common Issues

1. **"No logging system configured"**:
   - Make sure you've sourced the shell integration script
   - Check that `LEW_APP_DIR` is set correctly
   - Verify the shell integration loaded with: `echo "LEW shell integration loaded"`

2. **Commands not being captured**:
   - Restart your terminal after setup
   - Check if the log directory exists: `ls -la ~/lew_logs`
   - Verify shell hooks are active (you should see a brief message when sourcing)

3. **LEW not finding recent commands**:
   - Check log files: `ls -la ~/lew_logs/session_*.json`
   - Verify JSON format: `cat ~/lew_logs/session_*.json | head -5`

4. **Permission issues**:
   - Make sure the log directory is writable: `ls -ld ~/lew_logs`
   - Check Python script permissions: `ls -la app/terminal_logger.py`

### Debug Mode

Enable debug logging by adding to your shell configuration:

```bash
export LEW_DEBUG=1
```

This will show more detailed information about command capture and processing.

## 🔄 Migration from iTerm2 Version

If you're migrating from the iTerm2-only version:

1. **Backup your existing setup**:
   ```bash
   cp .env .env.backup
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

3. **The system will automatically fall back to iTerm2 logs** if they're configured and the new system isn't working

4. **Test both systems** to ensure smooth transition

## 🌟 Benefits of Terminal-Agnostic Version

- **Universal Compatibility**: Works in any terminal environment
- **Better Performance**: More efficient command capture and processing
- **Improved Reliability**: Better error handling and edge case management
- **Enhanced Security**: Safe command re-execution with whitelist approach
- **Future-Proof**: Not tied to any specific terminal application

## 🛠️ Development

### File Structure

```
app/
├── command.py              # Main LEW command (updated)
├── terminal_logger.py      # New terminal logging system
└── shell_integration.sh    # Shell hooks for command capture

setup.sh                    # Automated setup script
```

### Key Components

1. **TerminalLogger**: Handles command logging and retrieval
2. **Shell Integration**: Provides shell hooks for command capture
3. **Command Parser**: Updated to work with new logging format
4. **Fallback System**: Maintains compatibility with iTerm2 logs

## 📝 License

Same license as the original LEW project.

## 🤝 Contributing

Contributions are welcome! Please test on both Mac and Linux, and ensure compatibility with different terminal environments.

---

**Now LEW works everywhere! 🎉**