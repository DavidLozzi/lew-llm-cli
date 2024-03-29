import argparse
import glob
import httpx
import json
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ITERM2_LOGS = os.getenv("ITERM2_LOGS")


def get_latest_outputs(cnt):
    # Get a list of all log files
    log_files = glob.glob(os.path.expanduser(ITERM2_LOGS))

    # Find the newest log file
    newest_log_file = max(log_files, key=os.path.getctime)

    # Read the newest log file and split its content
    with open(newest_log_file, "r") as file:
        content = file.read()
        content = re.sub(
            r"^\[\d{2}/\d{2}/\d{4}, \d{1,2}:\d{2}:\d{2}\.\d{3}\s[AP]M\]\s", "", content
        )
        # remove the first character as its always duplicated from iTerm2
        split_content = [item[1:] for item in content.split("─╯")]
        outputs_to_send = "\n\n".join(split_content[-cnt - 1 : -1])

    for file in log_files:
        SECONDS_IN_A_WEEK = 7 * 24 * 60 * 60
        if os.path.getctime(file) < time.time() - SECONDS_IN_A_WEEK:
            os.remove(file)

    return outputs_to_send


def call_gpt(message, outputs_to_send):

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    request_body = {
        "messages": [
            {
                "role": "system",
                "content": """You are a GPT configured in a cli, your app name is `lew`.

You're goal is to support the user with command line interface (CLI) issues. \
They will send you the last command(s) they've executed along with the output of that command. They may send you more than one \
command and output or none at all. They may also include any additional comments or questions they may have.

You will review everything provided to you and you will provide a short and concise answer with the goal of resolving the \
user's issues. Your output will be streamed to the user's CLI, please format accordingly. For code or command snippets, \
wrap the code in ---.

If the user is talking about you, `lew`, here are your options:
- The first argument is a string, the message to send to the GPT, and is optional
- `--cnt` is optional and defaults to 1
- `lew "a message to send" to send to this GPT along with the last command and output
- `lew --cnt 2` to send the last 2 commands and outputs
- `lew --cnt 0` to chat with you and send no commands

Your options include:
- If you want to see the contents of a specific file, ask the user to run `cat filename.ext` and then tell them to run `lew --cnt 2`.
- If you want the user to run any specific command for you to view its output, instruct them to do so, and then tell them to run `lew --cnt 2`.
- If their request is ambiguous, ask for clarification, and instruct them to increment the `--cnt` value to keep the conversation history.
""",
            },
            {
                "role": "user",
                "content": f"""User's command and output:
                {outputs_to_send}
                {message}""",
            },
        ],
        "model": "gpt-4-turbo-preview",
        "temperature": 0.8,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "max_tokens": 800,
        "stream": True,
    }

    openai_url = "https://api.openai.com/v1/chat/completions"
    httpx_client = httpx.Client()
    print("\nCalling GPT to get your answer...\n", flush=True)
    with httpx_client.stream(
        method="POST", url=openai_url, json=request_body, headers=headers, timeout=60
    ) as response:
        if response.status_code != 200:
            print(f"Failed to call the API: {response.status_code}", flush=True)
            exit(1)
        for line in response.iter_lines():
            try:
                if line.strip():
                    val = line.replace("data: ", "", 1).strip()
                    if val == "[DONE]":
                        exit(1)
                    else:
                        chunk = json.loads(val)
                        if (
                            "choices" in chunk
                            and len(chunk["choices"]) > 0
                            and "delta" in chunk["choices"][0]
                            and "content" in chunk["choices"][0]["delta"]
                        ):
                            print(
                                chunk["choices"][0]["delta"]["content"],
                                end="",
                                flush=True,
                            )
            except Exception as e:
                print(f"\n\nError: {e}")
                print(line)
                exit(1)


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

    outputs_to_send = get_latest_outputs(args.cnt)

    if args.msg:
        message = f"Additional message from the user: {args.msg}"
    else:
        message = ""

    call_gpt(message, outputs_to_send)


if __name__ == "__main__":
    main()
