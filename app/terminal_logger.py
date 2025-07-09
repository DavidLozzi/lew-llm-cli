#!/usr/bin/env python3
"""
Terminal logger for capturing commands and output in any terminal.
This replaces the iTerm2-specific logging with a universal solution.
"""

import os
import sys
import json
import time
import re
import fcntl
import select
import subprocess
import signal
from datetime import datetime
from pathlib import Path


class TerminalLogger:
    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir or os.path.expanduser("~/lew_logs"))
        self.log_dir.mkdir(exist_ok=True)
        self.session_file = self.log_dir / f"session_{int(time.time())}.json"
        self.temp_output_file = self.log_dir / ".temp_output"
        self.command_delimiter = "--- LEW COMMAND ---"
        
    def clean_ansi_sequences(self, text):
        """Remove ANSI escape sequences from text"""
        # More comprehensive ANSI sequence removal
        ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # or [ for CSI, followed by the parameter bytes
                \[
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)
        return ansi_escape.sub('', text)
    
    def log_command(self, command, output="", exit_code=0):
        """Log a command and its output"""
        timestamp = datetime.now().isoformat()
        
        # Clean the output
        clean_output = self.clean_ansi_sequences(output)
        
        entry = {
            "timestamp": timestamp,
            "command": command,
            "output": clean_output,
            "exit_code": exit_code
        }
        
        # Append to session file
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_recent_commands(self, count=1):
        """Get the last N commands from the current session"""
        if not self.session_file.exists():
            return []
        
        commands = []
        try:
            with open(self.session_file, 'r') as f:
                for line in f:
                    if line.strip():
                        commands.append(json.loads(line.strip()))
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        
        return commands[-count:] if count > 0 else commands
    
    def format_for_lew(self, commands):
        """Format commands for LEW consumption"""
        if not commands:
            return ""
        
        formatted_parts = []
        for cmd in commands:
            timestamp = cmd.get('timestamp', '')
            command = cmd.get('command', '')
            output = cmd.get('output', '')
            
            # Format similar to iTerm2 logs
            formatted_parts.append(f"{command}\n{output}")
        
        return "\n\n".join(formatted_parts)
    
    def cleanup_old_logs(self, days=7):
        """Clean up log files older than specified days"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("session_*.json"):
            try:
                file_time = float(log_file.stem.split('_')[1])
                if file_time < cutoff_time:
                    log_file.unlink()
            except (ValueError, IndexError):
                # Skip files that don't match our naming pattern
                continue


def capture_command_output(command):
    """Capture both command and its output"""
    try:
        # Use script command to capture both input and output
        result = subprocess.run(
            ['script', '-q', '-c', command, '/dev/null'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", f"Error capturing output: {e}", 1


if __name__ == "__main__":
    # This can be used as a standalone script for testing or logging
    logger = TerminalLogger()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "log_entry" and len(sys.argv) >= 4:
            # Format: python terminal_logger.py log_entry "command" "output" "exit_code"
            command = sys.argv[2]
            output = sys.argv[3] if len(sys.argv) > 3 else ""
            exit_code = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            logger.log_command(command, output, exit_code)
        else:
            # Execute command and capture output
            command = " ".join(sys.argv[1:])
            stdout, stderr, exit_code = capture_command_output(command)
            output = stdout + stderr
            logger.log_command(command, output, exit_code)
            print(output)
    else:
        print("Usage: python terminal_logger.py <command>")
        print("   or: python terminal_logger.py log_entry 'command' 'output' 'exit_code'")