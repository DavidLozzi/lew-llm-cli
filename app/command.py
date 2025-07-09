import argparse
from dotenv import load_dotenv
import glob
import httpx
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from terminal_logger import TerminalLogger
    TERMINAL_LOGGER_AVAILABLE = True
except ImportError:
    TERMINAL_LOGGER_AVAILABLE = False

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ITERM2_LOGS = os.getenv("ITERM2_LOGS")
CLI_LOG_DELIMITER = os.getenv("CLI_LOG_DELIMITER")
LEW_LOG_DIR = os.getenv("LEW_LOG_DIR", os.path.expanduser("~/lew_logs"))
COMMAND_DELIM = "PLEASE RUN COMMAND"


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Create a TimedRotatingFileHandler for daily log rotation
file_handler = TimedRotatingFileHandler(
    os.path.expanduser("~/lew.log"), when="midnight", interval=1, backupCount=7
)
file_handler.setLevel(logging.INFO)

log_format = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(log_format)

log.addHandler(file_handler)

# Add handlers to the logger
log.addHandler(file_handler)


def get_latest_outputs(cnt):
    """
    Get the latest command outputs using the new terminal logger system.
    Falls back to iTerm2 logs if the new system isn't available.
    """
    try:
        # Try to use the new terminal logger first
        if TERMINAL_LOGGER_AVAILABLE:
            return get_latest_outputs_from_logger(cnt)
        
        # Fall back to iTerm2 logs if available
        if ITERM2_LOGS and CLI_LOG_DELIMITER:
            return get_latest_outputs_from_iterm2(cnt)
        
        # If neither is available, show a helpful message
        print("No logging system configured. Please set up terminal logging.")
        print("Run: source app/shell_integration.sh")
        return ""
        
    except Exception as e:
        log.error(f"get_latest_outputs: {e}")
        print(f"Failed to get the latest command outputs: {e}")
        return ""


def get_latest_outputs_from_logger(cnt):
    """Get outputs using the new terminal logger system"""
    try:
        logger = TerminalLogger(LEW_LOG_DIR)
        
        # Get recent commands from all session files
        all_commands = []
        log_dir = Path(LEW_LOG_DIR)
        
        # Get all session files, sorted by modification time (newest first)
        session_files = sorted(
            log_dir.glob("session_*.json"), 
            key=lambda x: x.stat().st_mtime, 
            reverse=True
        )
        
        # Read commands from session files until we have enough
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                command_data = json.loads(line.strip())
                                all_commands.append(command_data)
                            except json.JSONDecodeError:
                                continue
                
                # If we have enough commands, break
                if len(all_commands) >= cnt:
                    break
                    
            except FileNotFoundError:
                continue
        
        # Take the last cnt commands
        recent_commands = all_commands[-cnt:] if cnt > 0 else []
        
        # For commands without output, try to get safe command output
        enhanced_commands = []
        for cmd in recent_commands:
            command_text = cmd.get('command', '')
            output = cmd.get('output', '')
            
            # If no output and command is safe to re-run, try to get output
            if not output and is_safe_to_rerun(command_text):
                try:
                    result = subprocess.run(
                        command_text, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    output = result.stdout + result.stderr
                except (subprocess.TimeoutExpired, Exception):
                    output = ""
            
            enhanced_commands.append({
                'command': command_text,
                'output': output,
                'timestamp': cmd.get('timestamp', '')
            })
        
        # Format for LEW
        formatted_parts = []
        for cmd in enhanced_commands:
            formatted_parts.append(f"{cmd['command']}\n{cmd['output']}")
        
        outputs_to_send = "\n\n".join(formatted_parts)
        
        # Clean up old logs
        logger.cleanup_old_logs()
        
        return outputs_to_send
        
    except Exception as e:
        log.error(f"get_latest_outputs_from_logger: {e}")
        return ""


def get_latest_outputs_from_iterm2(cnt):
    """Original iTerm2 log parsing (fallback)"""
    try:
        # Get a list of all log files
        log_files = glob.glob(os.path.expanduser(ITERM2_LOGS))
        log.info(f"Log files from {ITERM2_LOGS}: {log_files}")

        # Find the newest log file
        newest_log_file = max(log_files, key=os.path.getctime)
        log.info(f"Newest log file: {newest_log_file}")

        # Read the newest log file and split its content
        with open(newest_log_file, "r") as file:
            content = file.read()
            content = re.sub(
                r"^\[\d{2}/\d{2}/\d{4}, \d{1,2}:\d{2}:\d{2}\.\d{3}\s[AP]M\]\s",
                "",
                content,
            )
            # after splitting the log on the username@computer, we remove the first part
            # david.lozzi@KHH9RGC0WN git % oopen ~/iterm2_logs/
            # ^  this is split out ^        ^ then we find the % and remove 3 characters
            #                                 after it as the command is always double keyed
            split_content = [
                item[item.find("%") + 3 :] for item in content.split(CLI_LOG_DELIMITER)
            ]
            outputs_to_send = "\n\n".join(split_content[-cnt - 1 : -1])

        for file in log_files:
            SECONDS_IN_A_WEEK = 7 * 24 * 60 * 60
            if os.path.getctime(file) < time.time() - SECONDS_IN_A_WEEK:
                os.remove(file)

        return outputs_to_send
    except Exception as e:
        log.error(f"get_latest_outputs_from_iterm2: {e}")
        return ""


def is_safe_to_rerun(command):
    """Check if a command is safe to re-run to get output"""
    # Commands that are safe to re-run (read-only operations)
    safe_commands = [
        'ls', 'pwd', 'whoami', 'date', 'uname', 'ps', 'df', 'du', 'free',
        'cat', 'head', 'tail', 'grep', 'find', 'which', 'type', 'wc',
        'git status', 'git log', 'git diff', 'git branch', 'git remote',
        'pip list', 'pip show', 'npm list', 'npm info',
        'docker ps', 'docker images', 'kubectl get', 'aws'
    ]
    
    # Commands that should never be re-run
    unsafe_commands = [
        'rm', 'rmdir', 'mv', 'cp', 'chmod', 'chown', 'kill', 'killall',
        'sudo', 'su', 'reboot', 'shutdown', 'mkfs', 'fdisk', 'dd',
        'git add', 'git commit', 'git push', 'git pull', 'git merge',
        'npm install', 'pip install', 'make', 'cmake', 'docker run',
        'docker build', 'kubectl apply', 'kubectl delete'
    ]
    
    command_lower = command.lower().strip()
    
    # Check if it's explicitly unsafe
    for unsafe in unsafe_commands:
        if command_lower.startswith(unsafe):
            return False
    
    # Check if it's explicitly safe
    for safe in safe_commands:
        if command_lower.startswith(safe):
            return True
    
    # Default to unsafe for unknown commands
    return False


def run_command(command):
    process = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    log.info(f"Running command: {command}")
    print(f"Running command: {command}")

    final_output = ""
    while True:
        # Check if there's output to read
        reads = [process.stdout.fileno(), process.stderr.fileno()]
        ret = select.select(reads, [], [])

        for fd in ret[0]:
            if fd == process.stdout.fileno():
                output = process.stdout.read1(1024).decode()
                if output:
                    print(output.strip())
                    final_output += output.strip()

        # If the command is asking for input, get it from the user
        if "Enter your input:" in final_output:
            user_input = input(final_output)
            process.stdin.write(user_input.encode())
            process.stdin.flush()

        # If the command has finished running, break the loop
        if process.poll() is not None:
            break

    # Print the final output
    # if final_output:
    #     print("\n---\nfinal", final_output, "---\n\n")

    return final_output


def run_commands(entire_message, user_message, original_outputs_to_send):
    pattern = re.compile(COMMAND_DELIM + "S?", re.IGNORECASE)
    all_commands = re.split(pattern, entire_message)[1].strip()

    commands_to_run = all_commands.split("\n")
    log.info(f"Commands to run: {commands_to_run}")
    commands_run = []
    while True:
        print("\n\nDo you want to run the commands?")
        answer = input("You may press CTRL+C at any time to stop them. (y/n): ").lower()
        print("")
        if answer in ["y", "yes"]:
            for command in commands_to_run:
                output = run_command(command)
                log.info(f"Command output: {output}")
                commands_run.append({"command": command, "output": output})

            if commands_run:
                commands_outputs = "\n\n".join(
                    [
                        f"Command:{command['command']}\nOutput:\n{command['output']}"
                        for command in commands_run
                    ]
                )
                new_outputs = f"\nGPT response:{entire_message}\n\nCommands run:\n{commands_outputs}"
                print(new_outputs)
                log.info(f"New outputs: {new_outputs}")
                call_gpt(user_message, new_outputs)
            return False
        elif answer in ["n", "no"]:
            log.info("User chose not to run the commands.")
            print("Okay, I won't run the commands.")
            return False
        else:
            log.info("User did not enter a valid answer.")
            print("Please enter yes or no.")


def call_gpt(message, outputs_to_send):

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    request_body = {
        "messages": [
            {
                "role": "system",
                "content": f"""You are lew, a GPT running in a command line interface (cli) on a Mac/Linux terminal.

# Your Goal
You're goal is to support the user with their CLI, through which they will be interacting with you. \
They may send you the last command(s) they've executed along with the output of that command. They may send you more than one \
command and output or none at all. They may also include any additional comments or questions they may have.

# Your Tasks
- Review everything provided to you
- Understand the intent and context
- Provide a short and concise answer with the goal of resolving the user's issues
- If their request is ambiguous, ask for clarification, and instruct them to increment the `--cnt` value to keep the conversation history.

# Your Output
- Your output will be streamed to the user's CLI, please format accordingly. For code or command snippets, \
wrap the code in ---.
- You can request the user to run commands for you:
  - If you want to run any specific command to view its output, provide one on each line: command args\ncommand args.
  - If the user asks you to create files, provide all the commands to create and insert the text as needed.
  - You can ask for contents of a specific file, use typical cli commands to read the file to the console and send it back to you.
  - Output the array at the end of your message, with comamnds on each line, do not combine commands. Format as:
    {COMMAND_DELIM}
    command args
    command args

# Additional Context
If the user is talking about you, `lew`, here are your cli options:
- The first argument is a string, the message to send to the GPT, and is optional
- `--cnt` is optional and defaults to 1, it is the number of command outputs to include in the message to you
- `lew "a message to send" will send you the message and the last command and output
- `lew --cnt 2` to send the last 2 commands and outputs
- `lew "message to send" --cnt 0` will send the message to you and send no commands""",
            },
            {
                "role": "user",
                "content": f"""{outputs_to_send}
                {message}""",
            },
        ],
        "model": "gpt-4o",
        "temperature": 0.8,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "max_tokens": 800,
        "stream": True,
    }

    openai_url = "https://api.openai.com/v1/chat/completions"
    httpx_client = httpx.Client(verify=False)
    entire_message = ""
    print("\n\033[92mCalling GPT to get your answer...\n", flush=True)
    log.info(f"Calling GPT with message: {message}\nOutputs: {outputs_to_send}")

    with httpx_client.stream(
        method="POST", url=openai_url, json=request_body, headers=headers, timeout=60
    ) as response:
        if response.status_code != 200:
            print(f"Failed to call the API: {response.status_code}", flush=True)
            log.error(
                f"call_gpt Failed to call the API: {response.status_code} {response}"
            )
            exit(1)

        for line in response.iter_lines():
            try:
                if line.strip():
                    val = line.replace("data: ", "", 1).strip()
                    if val == "[DONE]":
                        break
                    else:
                        chunk = json.loads(val)
                        if (
                            "choices" in chunk
                            and len(chunk["choices"]) > 0
                            and "delta" in chunk["choices"][0]
                            and "content" in chunk["choices"][0]["delta"]
                        ):
                            entire_message += chunk["choices"][0]["delta"]["content"]
                            print(
                                chunk["choices"][0]["delta"]["content"],
                                end="",
                                flush=True,
                            )
            except Exception as e:
                log.error(f"call_gpt {e}")
                print(f"\n\nError: {e}")
                print(line)
                exit(1)

    log.info(f"Entire message from GPT: {entire_message}")
    if COMMAND_DELIM in entire_message:
        print("\033[0m")
        log.info("Command delimiter exists, running commands")
        run_commands(entire_message, message, outputs_to_send)


def main():
    parser = argparse.ArgumentParser(description="Call GPT and stream its response.")
    parser.add_argument(
        "msg",
        nargs="?",
        help="Additional message to send to the LLM",
    )
    parser.add_argument(
        "--cnt",
        default=1,
        type=int,
        help="Number of command outputs to include in the message",
    )

    args = parser.parse_args()
    log.info(f"\n\nSTARTING SCRIPT. Arguments: {args}")

    outputs_to_send = f"User's command and output:\n{get_latest_outputs(args.cnt)}"

    if args.msg:
        message = f"Additional message from the user: {args.msg}"
    else:
        message = ""

    log.info(f"Message: {message}\nOutputs: {outputs_to_send}")
    call_gpt(message, outputs_to_send)


if __name__ == "__main__":
    main()
