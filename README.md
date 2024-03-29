# LEW - your LLM Enhanced Workflow in your cli

<img src="https://github.com/DavidLozzi/lew-llm-cli/blob/main/icon.jpeg" style="width:200px">

A powerfully simple tool for your CLI. Send your last commands to an LLM and get instant help!

Basic example:

<https://github.com/DavidLozzi/lew-llm-cli/assets/3543383/67161168-aca2-4fc9-bfb2-3a8dae6f1543>

LEW will also request to run commands to further support your request.

https://github.com/DavidLozzi/lew-llm-cli/assets/3543383/c88a2656-c265-4737-8f8a-18193add68bb


## Learn more

I will have a blog post up soon at davidlozzi.com

### Known Issues / Bugs

* Only works in iTerm2, doesn't work in VSCode terminal or other terminals where iTerm2 isn't in use.
* Will not work when SSH'd into another server.

### TODO

The current state of the utility is great, it has helped me a few times already. But there is more I want it to do:

_in no particular order_

* Switch to Anthropic just to check it out
* Improve logging capture, remove need for iTerm2 ([attempted with ZSH natively](/zsh%20logging.md))
* Allow user to specify which commands to send, instead of starting from the last command, i.e. send commands 2 and 3 I ran, not the immediate last one.
* Explore how to support when SSH'd in another server (is it as simple as following steps below except for the iTerm2 steps?)
* Currently the script only looks at the last log file, expand it to treat all logs as it's "db"
* Support Bash, PowerShell, Windows Command, and whatever else.
* ~~Allow the LLM to provide updated commands and enable the user to run them~~
* ~~Send contents of a file as desired to the LLM~~

## Set Up

### Prerequisites

To get started, you'll need:

1. Python v3 or later
1. [iTerm2](https://iterm2.com/) installed on your Mac
1. Clone this repo to your local machine
    1. Run `pip install -r requirements.txt` to install dependencies.
1. Copy the `.env.sample` file to `.env` (it will be ignored by git)
1. Get your OpenAI API Key from openai.com and update `.env` with your key.

### Configure

1. Open iTerm2 (prereqs #2), go to __Settings__
    1. In Settings, go to __Profiles__, then select your profile on the left (probably __Default__)
    1. Go to __Session__ on the right.
    1. Under __Miscellaneous__, check to enable __Automatically log session input to files in:__
    1. Also check to enable __Log plain text__ on the right
    1. Click the __Change__ button
    1. Currently, the code looks in `~/iterm2_logs/` for the logs from iTerm2.
        * Create a folder in the root called `iterm2_logs` and select that

            or

        * Create a folder where ever you want, and update the variable `ITERM2_LOGS` in `.env`
1. Edit your `~/.zshrc` file, you can do this by:
    1. If you have VSCode in your cli, enter `code ~/.zshrc`
    1. If you like vim, enter `vim ~/.zshrc`
    1. Or `open ~/`, then in Finder, press `CMD+SHIFT+.` to view hidden files then open the file in your editor of choice.
1. Add the following line:

    * `alias lew="python ~/git/lew-llm-cli/app/command.py"`
        * Update the location of the `command.py` file (prereqs #3)

### Some more notes

1. The python script `command.py` will clean up the `iterm2_logs` folder automatically, keeping only the last 7 days

## Running gli Co-Pilot

Real simple, after an error or command run, just enter `lew` and hit enter!

More detail:

```bash
lew "message to include" --cnt 2
```

* `"message to include"`, optional (default is empty), is a message you'd like to send along with the last command(s). You can explain what you're doing or whatever it is you need.
* `--cnt 2`, optional (default is 1), allows you to include more than 1 command and output to GPT, if you wanted to include the last 2 or more commands and their output, set the `cnt` parameter. You may also set `cnt` to `0` to have a chat with the bot without sending a command.

### Examples

__Help with a git command__

```bash
❯ git status
fatal: not a git repository (or any of the parent directories): .git
❯ lew

Calling GPT to get your answer...

The error message you're seeing, `fatal: not a git repository (or any of the parent directories): .git`, indicates that....
```

__Troubleshooting a specific file__

```bash
lew "my package file is messing up" --cnt 0                                                                                            ─╯

Calling GPT to get your answer...

To help you effectively, I need to know which package file you're referring to and what specific issue you're encountering. If it's a `package.json` for a Node.js project, or a different package file for another language or framework, please specify. Additionally, running a command that shows the error or problem you're facing with the package file can greatly help in diagnosing the issue.

If you can, please run the command that leads to the error, and then use:

---
lew --cnt 2
---

to send me the command along with its output. If it's an issue with the content of the package file itself, consider running:

---
cat path/to/packagefile
---

And then:

---
lew --cnt 2
---

to show me the contents of the file.%
```


__Chat without sending the last command__

```bash
lew "how do i list my director?" --cnt 0

Calling GPT to get your answer...

To list the contents of your current directory, please run the following command:

---
ls
---

This will show you all the files and directories in your current working directory.%

```

## Troubleshooting

Some common things I've run into:

* __`Failed to call the API: 401`__ - make sure your API key is correct.
* __Running `lew` responds to another command, not your last one.__ Are you running your current command in `iTerm2`? Can you see your command and output in the `iterm2_logs` folder you configured?

## Contribution

Yes please, coming soon, just fork it for now
